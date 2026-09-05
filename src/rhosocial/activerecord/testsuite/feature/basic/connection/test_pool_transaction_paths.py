# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_pool_transaction_paths.py
"""White-box contracts for `pool.transaction()` dispatch branches.

`BackendPool.transaction()` (python-activerecord
`connection/pool/sync_pool.py:540-598`) and its async counterpart
(`connection/pool/async_pool.py:579-638`) dispatch on context state
across three exclusive branches:

    Path 1  Already inside a transaction context     -> yield same backend
    Path 2  Inside a connection-only context         -> begin/commit on that
    Path 3  No existing context                      -> acquire + begin + release

These tests verify each branch's observable contract: backend identity,
token discipline via `context.*` helpers, and the cleanup path after an
exception. They are scoped to the pool layer; the underlying
TransactionManager state machine is exercised separately by
`test_savepoint_api.py` (T0-1).

Every test in this module MUST have an async twin in
`test_pool_transaction_paths_async.py`.
"""
import pytest

from rhosocial.activerecord.connection.pool import (
    get_current_transaction_backend,
    get_current_connection_backend,
    get_current_backend,
)


class TestSyncPath1ExistingTransactionIsReused:
    """Path 1 (sync_pool.py:561-565): inside a transaction, no new begin/commit.

    The inner `pool.transaction()` MUST yield the same backend instance
    and MUST NOT call begin/commit/rollback. Observable effect: the outer
    transaction remains active after the inner block exits, and the outer
    commit (not the inner) is what persists the data.
    """

    def test_inner_pool_transaction_yields_same_backend(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.transaction() as outer:
            with pool.transaction() as inner:
                assert inner is outer, \
                    "Expected the inner transaction backend to be the same as the outer one"

    def test_inner_exits_does_not_commit_outer(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.transaction() as outer:
            mgr = outer.transaction_manager
            assert mgr.is_active, "Expected the outer transaction manager to be active"
            with pool.transaction() as _:
                # still inside, level must not have changed by Path 1
                assert mgr.transaction_level == 1, \
                    "Expected the transaction level to stay at 1 inside Path 1 nesting"
            # After inner exits, outer still active at level 1
            assert mgr.is_active, "Expected the outer transaction manager to remain active"
            assert mgr.transaction_level == 1, \
                "Expected the transaction level to return to 1 after Path 1 exit"

    def test_path1_does_not_register_a_new_transaction_backend(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.transaction() as outer:
            with pool.transaction() as _inner:
                # ctx variable still resolves to exactly `outer`
                assert get_current_transaction_backend() is outer, \
                    "Expected the transaction token to still resolve to the outer backend"


class TestSyncPath2ConnectionOnlyBranch:
    """Path 2 (sync_pool.py:567-582): inside a connection-only context.

    A `with pool.connection()` block is open. `pool.transaction()` is
    entered inside that block. The transaction MUST operate on the same
    connection (no acquire), begin/commit issued on it, and after exit
    the connection-only context MUST remain usable and TX token MUST be
    cleared.
    """

    def test_transaction_reuses_the_connection_backend(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.connection() as conn:
            with pool.transaction() as tx_backend:
                assert tx_backend is conn, \
                    "Expected the transaction backend to reuse the connection backend"

    def test_tx_token_set_during_path2_and_cleared_after(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.connection():
            assert get_current_transaction_backend() is None, \
                "Expected no transaction token inside connection-only context"
            with pool.transaction() as tx:
                assert get_current_transaction_backend() is tx, \
                    "Expected the transaction token to point at the active transaction"
            # After exit, transaction token must be cleared even though
            # the connection-only token persists.
            assert get_current_transaction_backend() is None, \
                "Expected the transaction token to be cleared after Path 2 exit"
            # Connection token keeps pointing at the connection.
            assert get_current_connection_backend() is tx, \
                "Expected the connection token to persist after Path 2 exit"

    def test_path2_commits_visible_after_exit(self, sync_pool_and_model):
        pool, model = sync_pool_and_model
        with pool.connection():
            with pool.transaction() as backend:
                instance = model(name="Path2User", email="p2@test.local")
                instance.save()
        # Connection-only context exited; transaction must already be committed.
        with pool.connection() as _check:
            assert model.query().where("name = ?", ("Path2User",)).count() == 1, \
                "Expected the Path 2 commit to be visible after exit"

    def test_path2_rollback_on_exception_leaves_no_tx_token(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pytest.raises(RuntimeError):
            with pool.connection() as conn:
                with pool.transaction() as tx:
                    assert tx is conn, \
                        "Expected the transaction backend to be the same as the connection backend"
                    raise RuntimeError("boom")
        # After the entire nested context unwinds, nothing is bound.
        assert get_current_transaction_backend() is None, \
            "Expected the transaction token to be cleared after rollback"
        assert get_current_connection_backend() is None, \
            "Expected the connection token to be cleared after rollback"

    def test_path2_failure_does_not_break_outer_connection(self, sync_pool_and_model):
        """After Path 2 rollback, the connection backend remains reusable."""
        pool, model = sync_pool_and_model
        with pool.connection() as conn:
            try:
                with pool.transaction() as _tx:
                    raise RuntimeError("intentional")
            except RuntimeError:
                pass
            # The same connection ctx is still active, and writes outside
            # any nested transaction should auto-commit normally.
            assert not conn.transaction_manager.is_active, \
                "Expected no active transaction after the nested failure"
            instance = model(name="AfterFailure", email="af@test.local")
            instance.save()
        with pool.connection() as _check:
            assert model.query().where("name = ?", ("AfterFailure",)).count() == 1, \
                "Expected the post-failure write to be persisted"


class TestSyncPath3AcquireBranch:
    """Path 3 (sync_pool.py:584-598): no existing context, full acquire cycle."""

    def test_path3_yields_a_backend_bound_to_both_tx_and_conn_tokens(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.transaction() as backend:
            assert get_current_transaction_backend() is backend, \
                "Expected the transaction token to resolve to the Path 3 backend"
            assert get_current_connection_backend() is backend, \
                "Expected the connection token to resolve to the Path 3 backend"
            # get_current_backend resolves transaction first.
            assert get_current_backend() is backend, \
                "Expected get_current_backend() to resolve to the Path 3 backend"

    def test_path3_tokens_cleared_after_exit(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pool.transaction():
            pass
        assert get_current_transaction_backend() is None, \
            "Expected the transaction token to be cleared after Path 3 exit"
        assert get_current_connection_backend() is None, \
            "Expected the connection token to be cleared after Path 3 exit"
        assert get_current_backend() is None, \
            "Expected get_current_backend() to be cleared after Path 3 exit"

    def test_path3_commit_on_clean_exit(self, sync_pool_and_model):
        pool, model = sync_pool_and_model
        with pool.transaction() as _backend:
            model(name="P3Ok", email="p3ok@test.local").save()
        with pool.connection() as _check:
            assert model.query().where("name = ?", ("P3Ok",)).count() == 1, \
                "Expected the Path 3 commit to be visible after exit"

    def test_path3_rollback_on_exception(self, sync_pool_and_model):
        pool, model = sync_pool_and_model
        with pytest.raises(RuntimeError):
            with pool.transaction() as _backend:
                model(name="P3Fail", email="p3fail@test.local").save()
                raise RuntimeError("intentional")
        with pool.connection() as _check:
            assert model.query().where("name = ?", ("P3Fail",)).count() == 0, \
                "Expected the Path 3 write to be rolled back"

    def test_path3_tokens_cleared_after_exception(self, sync_pool_and_model):
        pool, _model = sync_pool_and_model
        with pytest.raises(RuntimeError):
            with pool.transaction():
                raise RuntimeError("intentional")
        assert get_current_transaction_backend() is None, \
            "Expected the transaction token to be cleared after Path 3 rollback"
        assert get_current_connection_backend() is None, \
            "Expected the connection token to be cleared after Path 3 rollback"


class TestSyncPathPrecedence:
    """The three branches are mutually exclusive and checked in order
    (transaction > connection > acquire). This precedence matters because
    path 1 never opens a savepoint on the outer TX: were path 2 to run
    when already inside a transaction, a second begin() would be issued
    on the same backend, which is a real semantic bug that the order
    guards against.
    """

    def test_transaction_context_beats_connection_only(self, sync_pool_and_model):
        """When both a transaction and connection token are set, transaction
        wins. Since `pool.transaction()` itself also sets the connection
        token (line 587), this verifies the precedence by checking identity.
        """
        pool, _model = sync_pool_and_model
        with pool.transaction() as tx:
            # Path 3 set both tokens to the same backend. A nested call
            # MUST take Path 1 (transaction wins), not Path 2.
            with pool.transaction() as inner:
                assert inner is tx, \
                    "Expected nested pool.transaction() to take Path 1 over Path 2"

    def test_no_savepoint_created_when_reentering_via_pool(self, sync_pool_and_model):
        """Path 1 must not create a savepoint.

        Pool-level nesting reuses the outer transaction; the
        TransactionManager's savepoint list must remain empty at the
        outer level. This is the critical guard against the historical
        bug where pool NESTED would double-begin on the same backend.
        """
        pool, _model = sync_pool_and_model
        with pool.transaction() as outer:
            mgr = outer.transaction_manager
            saved_sp = list(mgr._active_savepoints)
            with pool.transaction():
                # No new savepoint should have been registered.
                assert mgr._active_savepoints == saved_sp, \
                    "Expected Path 1 to register no new savepoints"
            assert mgr.transaction_level == 1, \
                "Expected the transaction level to remain at 1 across Path 1 nesting"
