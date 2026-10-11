# tests/rhosocial/activerecord/testsuite/core/test_pool.py
"""
Regression tests for the database pool's platform-specific slot locking.
"""
import sys

import pytest

from rhosocial.activerecord.testsuite.core import pool


@pytest.fixture
def no_fcntl(monkeypatch):
    """Make ``import fcntl`` fail the way it does on Windows."""
    monkeypatch.setitem(sys.modules, "fcntl", None)


class TestSerialRunNeedsNoPosixLocking:
    """A serial run never takes a slot lock, so it must not import ``fcntl``."""

    def test_pooling_is_inactive_without_xdist_worker(self, monkeypatch):
        """Without an xdist worker id there is nothing to pool."""
        monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
        assert pool.pooling_active() is False

    def test_release_all_without_held_slot_does_not_import_fcntl(self, no_fcntl):
        """The per-test teardown hook returns before touching ``fcntl``.

        The hook runs after *every* test, so importing the module
        unconditionally failed each test on Windows even though no slot lock
        had ever been taken.
        """
        assert pool._HELD == {}
        pool.release_all()


class TestSlotLocksRequirePosix:
    """Holding a slot implies the locks were taken, which is POSIX-only.

    A slot is only ever acquired by :func:`pool._acquire_slot`, which itself
    needs ``fcntl``; so the branch that unlocks is unreachable where ``fcntl``
    cannot be imported.  The import stays inside that branch rather than
    degrading to a silent no-op, because dropping the unlock would let two
    workers believe they own the same database.
    """

    def test_held_slot_reaches_the_locking_module(self, no_fcntl, tmp_path):
        """A held slot reaches ``fcntl`` -- and fails loudly without it."""
        lock_file = tmp_path / "slot.lock"
        with open(lock_file, "a+") as handle:
            pool._HELD["scenario"] = 0
            pool._OPEN_LOCKS[("scenario", 0)] = handle
            try:
                with pytest.raises(ImportError):
                    pool.release_all()
            finally:
                pool._HELD.pop("scenario", None)
                pool._OPEN_LOCKS.pop(("scenario", 0), None)