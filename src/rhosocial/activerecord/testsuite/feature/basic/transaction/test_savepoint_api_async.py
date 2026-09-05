# src/rhosocial/activerecord/testsuite/feature/basic/transaction/test_savepoint_api_async.py
"""Async black-box contracts for savepoint / release / rollback_to.

Mirror of test_savepoint_api.py exercising AsyncTransactionManager.
Every test in this module MUST have a sync twin in test_savepoint_api.py
to guarantee the sync/async symmetry required by the project's code style.
"""
import pytest

from rhosocial.activerecord.backend.errors import TransactionError


@pytest.fixture
async def async_txn_backend(async_pool_and_model):
    """Async fixture: open a transaction and yield the backend."""
    pool, _model = async_pool_and_model
    cm = pool.transaction()
    backend = await cm.__aenter__()
    try:
        yield backend
    finally:
        try:
            await cm.__aexit__(None, None, None)
        except Exception:
            pass


class TestAsyncSavepointCreate:
    """``AsyncTransactionManager.savepoint()`` creation contracts."""

    async def test_savepoint_autoname_is_returned_and_prefixed(self, async_txn_backend):
        """savepoint() with no name should return a non-empty string added to _active_savepoints."""
        mgr = async_txn_backend.transaction_manager
        name = await mgr.savepoint()
        assert isinstance(name, str), "Expected savepoint() to return a string name"
        assert name, "Expected the auto-generated savepoint name to be non-empty"
        assert name in mgr._active_savepoints, \
            "Expected the auto-named savepoint to be registered as active"

    async def test_savepoint_explicit_name_is_honored(self, async_txn_backend):
        """savepoint(name=...) should return and register the caller-provided name verbatim."""
        mgr = async_txn_backend.transaction_manager
        name = await mgr.savepoint(name="cust_sp_a")
        assert name == "cust_sp_a", "Expected savepoint() to return the explicit name"
        assert "cust_sp_a" in mgr._active_savepoints, \
            "Expected the explicit savepoint to be registered as active"

    async def test_savepoint_increments_active_savepoints(self, async_txn_backend):
        """Each savepoint() call should append to _active_savepoints in order."""
        mgr = async_txn_backend.transaction_manager
        before = len(mgr._active_savepoints)
        await mgr.savepoint(name="sp_first")
        await mgr.savepoint(name="sp_second")
        assert len(mgr._active_savepoints) == before + 2, \
            "Expected two new savepoints to be appended"
        assert mgr._active_savepoints[-1] == "sp_second", \
            "Expected the last savepoint to be 'sp_second'"
        assert mgr._active_savepoints[-2] == "sp_first", \
            "Expected the prior savepoint to be 'sp_first'"

    async def test_savepoint_seq_autoname_do_not_collide(self, async_txn_backend):
        """Three sequential auto-named savepoints must all be distinct."""
        mgr = async_txn_backend.transaction_manager
        names = {await mgr.savepoint() for _ in range(3)}
        assert len(names) == 3, "Expected three distinct auto-generated savepoint names"


class TestAsyncRelease:
    """``AsyncTransactionManager.release()`` contracts."""

    async def test_release_removes_named_savepoint(self, async_txn_backend):
        """release() should remove the named savepoint from _active_savepoints."""
        mgr = async_txn_backend.transaction_manager
        n = await mgr.savepoint(name="rel_target")
        assert n in mgr._active_savepoints, "Expected the savepoint to be active before release"
        await mgr.release(n)
        assert n not in mgr._active_savepoints, \
            "Expected the savepoint to be removed after release"

    async def test_release_does_not_touch_other_savepoints(self, async_txn_backend):
        """release() should only affect the named savepoint, leaving others untouched."""
        mgr = async_txn_backend.transaction_manager
        a = await mgr.savepoint(name="keep_a")
        b = await mgr.savepoint(name="rel_b")
        c = await mgr.savepoint(name="keep_c")
        await mgr.release(b)
        assert a in mgr._active_savepoints, "Expected 'keep_a' to remain active"
        assert c in mgr._active_savepoints, "Expected 'keep_c' to remain active"
        assert b not in mgr._active_savepoints, "Expected 'rel_b' to be released"

    async def test_release_unknown_name_raises(self, async_txn_backend):
        """release() on a name that was never created should raise TransactionError."""
        mgr = async_txn_backend.transaction_manager
        await mgr.savepoint(name="real_one")
        with pytest.raises(TransactionError):
            await mgr.release("never_created")

    async def test_release_outside_transaction_raises(self, async_pool_and_model):
        """release() outside an active transaction should raise TransactionError."""
        pool, _model = async_pool_and_model
        async with pool.connection() as backend:
            mgr = backend.transaction_manager
            assert not mgr.is_active, "Expected a fresh connection to be inactive"
            with pytest.raises(TransactionError):
                await mgr.release("any_sp")


class TestAsyncRollbackTo:
    """``AsyncTransactionManager.rollback_to()`` contracts."""

    async def test_rollback_to_truncates_newer_savepoints(self, async_txn_backend):
        """rollback_to(name) should drop savepoints created after ``name`` and keep it."""
        mgr = async_txn_backend.transaction_manager
        await mgr.savepoint(name="lvl1")
        await mgr.savepoint(name="lvl2")
        await mgr.savepoint(name="lvl3")
        await mgr.savepoint(name="lvl4")
        await mgr.rollback_to("lvl2")
        assert "lvl2" in mgr._active_savepoints, "Expected 'lvl2' to be retained"
        assert "lvl1" in mgr._active_savepoints, "Expected 'lvl1' to be retained"
        assert "lvl3" not in mgr._active_savepoints, "Expected 'lvl3' to be truncated"
        assert "lvl4" not in mgr._active_savepoints, "Expected 'lvl4' to be truncated"
        assert mgr._active_savepoints == ["lvl1", "lvl2"], \
            "Expected _active_savepoints to be truncated to ['lvl1', 'lvl2']"

    async def test_rollback_to_oldest_keeps_all_older(self, async_txn_backend):
        """rollback_to() to the oldest savepoint should retain only that one."""
        mgr = async_txn_backend.transaction_manager
        await mgr.savepoint(name="a")
        await mgr.savepoint(name="b")
        await mgr.savepoint(name="c")
        await mgr.rollback_to("a")
        assert mgr._active_savepoints == ["a"], \
            "Expected _active_savepoints to be truncated to ['a']"

    async def test_rollback_to_same_savepoint_keeps_it(self, async_txn_backend):
        """Rolling back to the top savepoint should keep it active."""
        mgr = async_txn_backend.transaction_manager
        top = await mgr.savepoint(name="top")
        await mgr.rollback_to(top)
        assert top in mgr._active_savepoints, \
            "Expected the top savepoint to remain active after rollback_to"

    async def test_rollback_to_unknown_raises(self, async_txn_backend):
        """rollback_to() on an unknown savepoint name should raise TransactionError."""
        mgr = async_txn_backend.transaction_manager
        await mgr.savepoint(name="actual")
        with pytest.raises(TransactionError):
            await mgr.rollback_to("phantom")

    async def test_rollback_to_outside_transaction_raises(self, async_pool_and_model):
        """rollback_to() outside an active transaction should raise TransactionError."""
        pool, _model = async_pool_and_model
        async with pool.connection() as backend:
            mgr = backend.transaction_manager
            assert not mgr.is_active, "Expected a fresh connection to be inactive"
            with pytest.raises(TransactionError):
                await mgr.rollback_to("any_sp")


class TestAsyncSavepointOutsideTransaction:
    """``savepoint()`` itself requires an active transaction."""

    async def test_savepoint_outside_transaction_raises(self, async_pool_and_model):
        """savepoint() on an inactive manager should raise TransactionError."""
        pool, _model = async_pool_and_model
        async with pool.connection() as backend:
            mgr = backend.transaction_manager
            assert not mgr.is_active, "Expected a fresh connection to be inactive"
            with pytest.raises(TransactionError):
                await mgr.savepoint(name="orphan_sp")


class TestAsyncSavepointDataSemantics:
    """``rollback_to`` actually rolls back DML done after the savepoint."""

    async def test_rollback_to_discards_writes_after_savepoint(self, async_pool_and_model):
        """Writes performed after a savepoint should be undone by rollback_to()."""
        pool, model = async_pool_and_model
        async with pool.transaction() as backend:
            mgr = backend.transaction_manager
            await mgr.savepoint(name="before_changes")
            instance = model(name="Alice", email="alice@test.local")
            await instance.save()
            assert await model.query().where("name = ?", ("Alice",)).count() == 1, \
                "Expected Alice's row to be visible inside the transaction"
            await mgr.rollback_to("before_changes")
            assert await model.query().where("name = ?", ("Alice",)).count() == 0, \
                "Expected Alice's row to be discarded after rollback_to"


class TestAsyncCommitWithPendingSavepoint:
    """Outer commit still succeeds when savepoints are unreleased."""

    async def test_outer_commit_with_unreleased_savepoint_succeeds(self, async_pool_and_model):
        """Outermost commit should release lingering savepoints and persist DML."""
        pool, model = async_pool_and_model
        async with pool.transaction() as backend:
            mgr = backend.transaction_manager
            await mgr.savepoint(name="left_open")
            instance = model(name="Bob", email="bob@test.local")
            await instance.save()
        async with pool.connection() as _backend:
            assert await model.query().where("name = ?", ("Bob",)).count() == 1, \
                "Expected Bob's row to be persisted after outer commit"
