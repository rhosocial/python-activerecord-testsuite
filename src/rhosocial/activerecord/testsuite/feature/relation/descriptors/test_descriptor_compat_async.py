# src/rhosocial/activerecord/testsuite/feature/relation/descriptors/test_descriptor_compat_async.py
"""
Tests for sync/async descriptor compatibility.

Sync descriptors (BelongsTo, HasMany, HasOne) must not be used on async models
(AsyncActiveRecord), and async descriptors (AsyncBelongsTo, AsyncHasMany, AsyncHasOne)
must not be used on sync models (ActiveRecord). Mixing them raises TypeError
at class creation time.
"""
import pytest
from typing import ClassVar, Optional


class TestSyncDescriptorOnAsyncModel:
    """Sync descriptors on async models raise TypeError at class creation."""

    async def test_sync_belongs_to_on_async_model_raises(self):
        """Sync BelongsTo on AsyncActiveRecord raises TypeError."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        from rhosocial.activerecord.relation.descriptors import BelongsTo

        with pytest.raises(TypeError, match="Sync relation descriptor.*async model"):
            class AsyncB(AsyncActiveRecord):
                __table_name__ = "compat_b"
                id: Optional[int] = None
                ref_id: int
                a: ClassVar[BelongsTo["AsyncA"]] = BelongsTo(
                    foreign_key="ref_id", inverse_of=None
                )

    async def test_sync_has_many_on_async_model_raises(self):
        """Sync HasMany on AsyncActiveRecord raises TypeError."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        from rhosocial.activerecord.relation.descriptors import HasMany

        with pytest.raises(TypeError, match="Sync relation descriptor.*async model"):
            class AsyncP(AsyncActiveRecord):
                __table_name__ = "compat_p"
                id: Optional[int] = None
                items: ClassVar[HasMany["AsyncC"]] = HasMany(
                    foreign_key="parent_id", inverse_of=None
                )

    async def test_sync_has_one_on_async_model_raises(self):
        """Sync HasOne on AsyncActiveRecord raises TypeError."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        from rhosocial.activerecord.relation.descriptors import HasOne

        with pytest.raises(TypeError, match="Sync relation descriptor.*async model"):
            class AsyncU(AsyncActiveRecord):
                __table_name__ = "compat_u"
                id: Optional[int] = None
                profile: ClassVar[HasOne["AsyncPr"]] = HasOne(
                    foreign_key="user_id", inverse_of=None
                )


class TestAsyncDescriptorOnSyncModel:
    """Async descriptors on sync models raise TypeError at class creation."""

    async def test_async_belongs_to_on_sync_model_raises(self):
        """Async BelongsTo on ActiveRecord raises TypeError."""
        from rhosocial.activerecord.model import ActiveRecord
        from rhosocial.activerecord.relation.async_descriptors import AsyncBelongsTo

        with pytest.raises(TypeError, match="Async relation descriptor.*sync model"):
            class SyncB(ActiveRecord):
                __table_name__ = "compat_sb"
                id: Optional[int] = None
                ref_id: int
                a: ClassVar[AsyncBelongsTo["SyncA"]] = AsyncBelongsTo(
                    foreign_key="ref_id", inverse_of=None
                )

    async def test_async_has_many_on_sync_model_raises(self):
        """Async HasMany on ActiveRecord raises TypeError."""
        from rhosocial.activerecord.model import ActiveRecord
        from rhosocial.activerecord.relation.async_descriptors import AsyncHasMany

        with pytest.raises(TypeError, match="Async relation descriptor.*sync model"):
            class SyncP(ActiveRecord):
                __table_name__ = "compat_sp"
                id: Optional[int] = None
                items: ClassVar[AsyncHasMany["SyncC"]] = AsyncHasMany(
                    foreign_key="parent_id", inverse_of=None
                )

    async def test_async_has_one_on_sync_model_raises(self):
        """Async HasOne on ActiveRecord raises TypeError."""
        from rhosocial.activerecord.model import ActiveRecord
        from rhosocial.activerecord.relation.async_descriptors import AsyncHasOne

        with pytest.raises(TypeError, match="Async relation descriptor.*sync model"):
            class SyncU(ActiveRecord):
                __table_name__ = "compat_su"
                id: Optional[int] = None
                profile: ClassVar[AsyncHasOne["SyncPr"]] = AsyncHasOne(
                    foreign_key="user_id", inverse_of=None
                )


class TestCorrectUsageNoError:
    """Correct descriptor usage should not raise."""

    async def test_sync_descriptor_on_sync_model_ok(self):
        """Sync BelongsTo on ActiveRecord works without error."""
        from rhosocial.activerecord.model import ActiveRecord
        from rhosocial.activerecord.relation.descriptors import BelongsTo

        class SyncB(ActiveRecord):
            __table_name__ = "compat_nw_sb"
            id: Optional[int] = None
            ref_id: int
            a: ClassVar[BelongsTo["SyncA"]] = BelongsTo(
                foreign_key="ref_id", inverse_of=None
            )

    async def test_async_descriptor_on_async_model_ok(self):
        """Async BelongsTo on AsyncActiveRecord works without error."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        from rhosocial.activerecord.relation.async_descriptors import AsyncBelongsTo

        class AsyncB(AsyncActiveRecord):
            __table_name__ = "compat_nw_ab"
            id: Optional[int] = None
            ref_id: int
            a: ClassVar[AsyncBelongsTo["AsyncA"]] = AsyncBelongsTo(
                foreign_key="ref_id", inverse_of=None
            )
