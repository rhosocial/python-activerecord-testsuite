# src/rhosocial/activerecord/testsuite/feature/relation/test_descriptor_compat.py
"""
Tests for sync/async descriptor compatibility.

Sync descriptors (BelongsTo, HasMany, HasOne) on async models and async descriptors
(AsyncBelongsTo, AsyncHasMany, AsyncHasOne) on sync models do not raise explicit
errors, but silently fail to load data. These tests document that behavior to
prevent accidental misuse.
"""
import pytest
from typing import ClassVar, Optional


class TestSyncDescriptorOnAsyncModel:
    """Sync descriptors on async models silently fail to load data."""

    def test_sync_belongs_to_on_async_model_returns_none(self):
        """Sync BelongsTo on AsyncActiveRecord returns None (no backend configured)."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        from rhosocial.activerecord.relation.descriptors import BelongsTo

        class AsyncA(AsyncActiveRecord):
            __table_name__ = "compat_a"
            id: Optional[int] = None
            ref_id: int

        class AsyncB(AsyncActiveRecord):
            __table_name__ = "compat_b"
            id: Optional[int] = None
            a: ClassVar[BelongsTo["AsyncA"]] = BelongsTo(
                foreign_key="ref_id", inverse_of=None
            )

        b = AsyncB(id=1, ref_id=1)
        result = b.a()
        assert result is None

    def test_sync_has_many_on_async_model_returns_none(self):
        """Sync HasMany on AsyncActiveRecord returns None (no backend configured)."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        from rhosocial.activerecord.relation.descriptors import HasMany

        class AsyncP(AsyncActiveRecord):
            __table_name__ = "compat_p"
            id: Optional[int] = None
            items: ClassVar[HasMany["AsyncC"]] = HasMany(
                foreign_key="parent_id", inverse_of=None
            )

        class AsyncC(AsyncActiveRecord):
            __table_name__ = "compat_c"
            id: Optional[int] = None
            parent_id: int

        p = AsyncP(id=1)
        result = p.items()
        assert result is None


class TestAsyncDescriptorOnSyncModel:
    """Async descriptors on sync models return unawaited coroutines."""

    def test_async_belongs_to_on_sync_model_returns_coroutine(self):
        """Async BelongsTo on ActiveRecord returns a coroutine (not a model)."""
        from rhosocial.activerecord.model import ActiveRecord
        from rhosocial.activerecord.relation.async_descriptors import AsyncBelongsTo
        import asyncio

        class SyncA(ActiveRecord):
            __table_name__ = "compat_sa"
            id: Optional[int] = None
            ref_id: int

        class SyncB(ActiveRecord):
            __table_name__ = "compat_sb"
            id: Optional[int] = None
            a: ClassVar[AsyncBelongsTo["SyncA"]] = AsyncBelongsTo(
                foreign_key="ref_id", inverse_of=None
            )

        b = SyncB(id=1, ref_id=1)
        result = b.a()
        assert asyncio.iscoroutine(result)
        result.close()

    def test_async_has_many_on_sync_model_returns_coroutine(self):
        """Async HasMany on ActiveRecord returns a coroutine (not a list)."""
        from rhosocial.activerecord.model import ActiveRecord
        from rhosocial.activerecord.relation.async_descriptors import AsyncHasMany
        import asyncio

        class SyncP(ActiveRecord):
            __table_name__ = "compat_sp"
            id: Optional[int] = None
            items: ClassVar[AsyncHasMany["SyncC"]] = AsyncHasMany(
                foreign_key="parent_id", inverse_of=None
            )

        class SyncC(ActiveRecord):
            __table_name__ = "compat_sc"
            id: Optional[int] = None
            parent_id: int

        p = SyncP(id=1)
        result = p.items()
        assert asyncio.iscoroutine(result)
        result.close()
