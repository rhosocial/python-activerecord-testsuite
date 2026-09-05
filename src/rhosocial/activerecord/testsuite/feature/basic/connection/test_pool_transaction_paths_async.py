# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_pool_transaction_paths_async.py
"""Async white-box contracts for `pool.transaction()` dispatch branches.

Mirror of test_pool_transaction_paths.py exercising AsyncBackendPool
(`connection/pool/async_pool.py:579-638`). Every test MUST have a sync
twin in test_pool_transaction_paths.py to guarantee the sync/async
symmetry required by the project code style.
"""
import pytest

from rhosocial.activerecord.connection.pool import (
    get_current_async_transaction_backend,
    get_current_async_connection_backend,
    get_current_async_backend,
)


class TestAsyncPath1ExistingTransactionIsReused:
    """Async Path 1: inside a transaction, no new begin/commit."""

    async def test_inner_pool_transaction_yields_same_backend(self, async_pool_and_model):
        """Inner pool.transaction() should yield the same backend as the outer one."""
        pool, _model = async_pool_and_model
        async with pool.transaction() as outer:
            async with pool.transaction() as inner:
                assert inner is outer, \
                    "Expected the inner transaction backend to be the same as the outer one"

    async def test_inner_exits_does_not_commit_outer(self, async_pool_and_model):
        """The inner transaction exit must not commit or close the outer transaction."""
        pool, _model = async_pool_and_model
        async with pool.transaction() as outer:
            mgr = outer.transaction_manager
            assert mgr.is_active, "Expected the outer transaction manager to be active"
            async with pool.transaction() as _:
                assert mgr.transaction_level == 1, \
                    "Expected the transaction level to stay at 1 inside Path 1 nesting"
            assert mgr.is_active, "Expected the outer transaction manager to remain active"
            assert mgr.transaction_level == 1, \
                "Expected the transaction level to return to 1 after Path 1 exit"

    async def test_path1_does_not_register_a_new_transaction_backend(self, async_pool_and_model):
        """Path 1 must not register a new transaction backend on the async token."""
        pool, _model = async_pool_and_model
        async with pool.transaction() as outer:
            async with pool.transaction() as _inner:
                assert get_current_async_transaction_backend() is outer, \
                    "Expected the async transaction token to still resolve to the outer backend"


class TestAsyncPath2ConnectionOnlyBranch:
    """Async Path 2: inside a connection-only context."""

    async def test_transaction_reuses_the_connection_backend(self, async_pool_and_model):
        """pool.transaction() inside a connection context must reuse the connection backend."""
        pool, _model = async_pool_and_model
        async with pool.connection() as conn:
            async with pool.transaction() as tx_backend:
                assert tx_backend is conn, \
                    "Expected the transaction backend to reuse the connection backend"

    async def test_tx_token_set_during_path2_and_cleared_after(self, async_pool_and_model):
        """The async transaction token is set during Path 2 and cleared after exit."""
        pool, _model = async_pool_and_model
        async with pool.connection():
            assert get_current_async_transaction_backend() is None, \
                "Expected no transaction token inside connection-only context"
            async with pool.transaction() as tx:
                assert get_current_async_transaction_backend() is tx, \
                    "Expected the transaction token to point at the active transaction"
            assert get_current_async_transaction_backend() is None, \
                "Expected the transaction token to be cleared after Path 2 exit"
            assert get_current_async_connection_backend() is tx, \
                "Expected the connection token to persist after Path 2 exit"

    async def test_path2_commits_visible_after_exit(self, async_pool_and_model):
        """Writes inside Path 2 should be visible after the inner block exits."""
        pool, model = async_pool_and_model
        async with pool.connection():
            async with pool.transaction() as _backend:
                instance = model(name="Path2User", email="p2@test.local")
                await instance.save()
        async with pool.connection() as _check:
            assert await model.query().where("name = ?", ("Path2User",)).count() == 1, \
                "Expected the Path 2 commit to be visible after exit"

    async def test_path2_rollback_on_exception_leaves_no_tx_token(self, async_pool_and_model):
        """A Path 2 exception must leave no transaction or connection token bound."""
        pool, _model = async_pool_and_model
        with pytest.raises(RuntimeError):
            async with pool.connection() as conn:
                async with pool.transaction() as tx:
                    assert tx is conn, \
                        "Expected the transaction backend to be the same as the connection backend"
                    raise RuntimeError("boom")
        assert get_current_async_transaction_backend() is None, \
            "Expected the transaction token to be cleared after rollback"
        assert get_current_async_connection_backend() is None, \
            "Expected the connection token to be cleared after rollback"

    async def test_path2_failure_does_not_break_outer_connection(self, async_pool_and_model):
        """After Path 2 rollback, the connection backend must remain reusable."""
        pool, model = async_pool_and_model
        async with pool.connection() as conn:
            try:
                async with pool.transaction() as _tx:
                    raise RuntimeError("intentional")
            except RuntimeError:
                pass
            assert not conn.transaction_manager.is_active, \
                "Expected no active transaction after the nested failure"
            instance = model(name="AfterFailure", email="af@test.local")
            await instance.save()
        async with pool.connection() as _check:
            assert await model.query().where("name = ?", ("AfterFailure",)).count() == 1, \
                "Expected the post-failure write to be persisted"


class TestAsyncPath3AcquireBranch:
    """Async Path 3: no existing context, full acquire cycle."""

    async def test_path3_yields_a_backend_bound_to_both_tx_and_conn_tokens(self, async_pool_and_model):
        """Path 3 should yield a backend bound to both async tokens."""
        pool, _model = async_pool_and_model
        async with pool.transaction() as backend:
            assert get_current_async_transaction_backend() is backend, \
                "Expected the transaction token to resolve to the Path 3 backend"
            assert get_current_async_connection_backend() is backend, \
                "Expected the connection token to resolve to the Path 3 backend"
            assert get_current_async_backend() is backend, \
                "Expected get_current_async_backend() to resolve to the Path 3 backend"

    async def test_path3_tokens_cleared_after_exit(self, async_pool_and_model):
        """All async tokens should be cleared after Path 3 exits cleanly."""
        pool, _model = async_pool_and_model
        async with pool.transaction():
            pass
        assert get_current_async_transaction_backend() is None, \
            "Expected the transaction token to be cleared after Path 3 exit"
        assert get_current_async_connection_backend() is None, \
            "Expected the connection token to be cleared after Path 3 exit"
        assert get_current_async_backend() is None, \
            "Expected get_current_async_backend() to be cleared after Path 3 exit"

    async def test_path3_commit_on_clean_exit(self, async_pool_and_model):
        """Writes inside Path 3 should be committed on clean exit."""
        pool, model = async_pool_and_model
        async with pool.transaction() as _backend:
            u = model(name="P3Ok", email="p3ok@test.local")
            await u.save()
        async with pool.connection() as _check:
            assert await model.query().where("name = ?", ("P3Ok",)).count() == 1, \
                "Expected the Path 3 commit to be visible after exit"

    async def test_path3_rollback_on_exception(self, async_pool_and_model):
        """Writes inside Path 3 should be rolled back when an exception is raised."""
        pool, model = async_pool_and_model
        with pytest.raises(RuntimeError):
            async with pool.transaction() as _backend:
                u = model(name="P3Fail", email="p3fail@test.local")
                await u.save()
                raise RuntimeError("intentional")
        async with pool.connection() as _check:
            assert await model.query().where("name = ?", ("P3Fail",)).count() == 0, \
                "Expected the Path 3 write to be rolled back"

    async def test_path3_tokens_cleared_after_exception(self, async_pool_and_model):
        """All async tokens should be cleared after Path 3 rollback."""
        pool, _model = async_pool_and_model
        with pytest.raises(RuntimeError):
            async with pool.transaction():
                raise RuntimeError("intentional")
        assert get_current_async_transaction_backend() is None, \
            "Expected the transaction token to be cleared after Path 3 rollback"
        assert get_current_async_connection_backend() is None, \
            "Expected the connection token to be cleared after Path 3 rollback"


class TestAsyncPathPrecedence:
    """Async precedence among Path 1, Path 2, and Path 3 (transaction wins)."""

    async def test_transaction_context_beats_connection_only(self, async_pool_and_model):
        """Nested pool.transaction() must take Path 1 over Path 2 when already inside a TX."""
        pool, _model = async_pool_and_model
        async with pool.transaction() as tx:
            async with pool.transaction() as inner:
                assert inner is tx, \
                    "Expected nested pool.transaction() to take Path 1 over Path 2"

    async def test_no_savepoint_created_when_reentering_via_pool(self, async_pool_and_model):
        """Path 1 must not register any new savepoints."""
        pool, _model = async_pool_and_model
        async with pool.transaction() as outer:
            mgr = outer.transaction_manager
            saved_sp = list(mgr._active_savepoints)
            async with pool.transaction():
                assert mgr._active_savepoints == saved_sp, \
                    "Expected Path 1 to register no new savepoints"
            assert mgr.transaction_level == 1, \
                "Expected the transaction level to remain at 1 across Path 1 nesting"
