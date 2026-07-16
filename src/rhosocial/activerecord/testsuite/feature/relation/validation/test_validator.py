# src/rhosocial/activerecord/testsuite/feature/relation/validation/test_validator.py
"""
Tests for RelationshipValidator and AsyncRelationshipValidator.

Covers: valid/invalid BelongsTo<->HasMany, BelongsTo<->HasOne pairings,
inverse_of auto-setting when missing on the other side, and missing-inverse
detection via get_related_model() — for both sync (BaseModel) and async
(AsyncActiveRecord) descriptor pairs.
"""
import pytest
from typing import ClassVar, Optional

from pydantic import BaseModel

from rhosocial.activerecord.relation.base import RelationManagementMixin
from rhosocial.activerecord.relation.descriptors import (
    BelongsTo, HasOne, HasMany, RelationshipValidator, RelationDescriptor
)
from rhosocial.activerecord.relation.async_descriptors import (
    AsyncBelongsTo, AsyncHasOne, AsyncHasMany, AsyncRelationshipValidator,
    AsyncRelationDescriptor
)


# ── Sync Validator Tests ──────────────────────────────────

class TestSyncRelationshipValidator:
    """Tests for RelationshipValidator with valid pairs."""

    def test_belongs_to_has_many_valid(self):
        """BelongsTo <-> HasMany is a valid pair."""
        class Related(RelationManagementMixin, BaseModel):
            id: int
            owner_id: int
            owner: ClassVar[BelongsTo["Owner"]] = BelongsTo(
                foreign_key="owner_id", inverse_of="items"
            )

        class Owner(RelationManagementMixin, BaseModel):
            id: int
            items: ClassVar[HasMany["Related"]] = HasMany(
                foreign_key="owner_id", inverse_of="owner"
            )

        # Trigger validation by resolving the relation
        rel = Owner.get_relation("items")
        model = rel.get_related_model(Owner)
        assert model is not None

    def test_belongs_to_has_one_valid(self):
        """BelongsTo <-> HasOne is a valid pair."""
        class Profile(RelationManagementMixin, BaseModel):
            id: int
            user_id: int
            user: ClassVar[BelongsTo["User"]] = BelongsTo(
                foreign_key="user_id", inverse_of="profile"
            )

        class User(RelationManagementMixin, BaseModel):
            id: int
            profile: ClassVar[HasOne["Profile"]] = HasOne(
                foreign_key="user_id", inverse_of="user"
            )

        rel = User.get_relation("profile")
        model = rel.get_related_model(User)
        assert model is not None

    def test_invalid_pair_raises(self):
        """BelongsTo <-> BelongsTo should raise ValueError."""
        class Other(RelationManagementMixin, BaseModel):
            id: int
            ref_id: int
            item: ClassVar[BelongsTo["Item"]] = BelongsTo(
                foreign_key="ref_id", inverse_of="other"
            )

        class Item(RelationManagementMixin, BaseModel):
            id: int
            other_id: int
            other: ClassVar[BelongsTo["Other"]] = BelongsTo(
                foreign_key="other_id", inverse_of="item"
            )

        rel = Item.get_relation("other")
        with pytest.raises(ValueError, match="Invalid relationship pair"):
            rel.get_related_model(Item)

    def test_missing_inverse_raises(self):
        """Missing inverse relationship should raise ValueError."""
        class Related(RelationManagementMixin, BaseModel):
            id: int
            owner_id: int

        class Owner(RelationManagementMixin, BaseModel):
            id: int
            items: ClassVar[HasMany["Related"]] = HasMany(
                foreign_key="owner_id", inverse_of="nonexistent"
            )

        rel = Owner.get_relation("items")
        with pytest.raises(ValueError, match="not found"):
            rel.get_related_model(Owner)

    def test_auto_set_inverse_of(self):
        """Validator should auto-set inverse_of when missing."""
        class Related(RelationManagementMixin, BaseModel):
            id: int
            owner_id: int
            owner: ClassVar[BelongsTo["Owner"]] = BelongsTo(
                foreign_key="owner_id"
            )

        class Owner(RelationManagementMixin, BaseModel):
            id: int
            items: ClassVar[HasMany["Related"]] = HasMany(
                foreign_key="owner_id", inverse_of="owner"
            )

        rel = Owner.get_relation("items")
        rel.get_related_model(Owner)
        # The validator should have set inverse_of on the Related.owner descriptor
        related_rel = Related.get_relation("owner")
        assert related_rel.inverse_of == "items"

# ── Async Validator Tests ─────────────────────────────────

class TestAsyncRelationshipValidator:
    """Tests for AsyncRelationshipValidator."""

    def test_async_belongs_to_has_many_valid(self):
        """AsyncBelongsTo <-> AsyncHasMany is a valid pair."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncRelated(AsyncActiveRecord):
            __table_name__ = "v_abhm_rel"
            id: Optional[int] = None
            owner_id: int
            owner: ClassVar[AsyncBelongsTo["AsyncOwner"]] = AsyncBelongsTo(
                foreign_key="owner_id", inverse_of="items"
            )

        class AsyncOwner(AsyncActiveRecord):
            __table_name__ = "v_abhm_own"
            id: Optional[int] = None
            items: ClassVar[AsyncHasMany["AsyncRelated"]] = AsyncHasMany(
                foreign_key="owner_id", inverse_of="owner"
            )

        rel = AsyncOwner.get_relation("items")
        model = rel.get_related_model(AsyncOwner)
        assert model is not None

    def test_async_belongs_to_has_one_valid(self):
        """AsyncBelongsTo <-> AsyncHasOne is a valid pair."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncProfile(AsyncActiveRecord):
            __table_name__ = "v_abho_pro"
            id: Optional[int] = None
            user_id: int
            user: ClassVar[AsyncBelongsTo["AsyncUser"]] = AsyncBelongsTo(
                foreign_key="user_id", inverse_of="profile"
            )

        class AsyncUser(AsyncActiveRecord):
            __table_name__ = "v_abho_usr"
            id: Optional[int] = None
            profile: ClassVar[AsyncHasOne["AsyncProfile"]] = AsyncHasOne(
                foreign_key="user_id", inverse_of="user"
            )

        rel = AsyncUser.get_relation("profile")
        model = rel.get_related_model(AsyncUser)
        assert model is not None

    def test_async_invalid_pair_raises(self):
        """AsyncBelongsTo <-> AsyncBelongsTo should raise ValueError."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncOther(AsyncActiveRecord):
            __table_name__ = "v_ip_oth"
            id: Optional[int] = None
            ref_id: int
            item: ClassVar[AsyncBelongsTo["AsyncItem"]] = AsyncBelongsTo(
                foreign_key="ref_id", inverse_of="other"
            )

        class AsyncItem(AsyncActiveRecord):
            __table_name__ = "v_ip_itm"
            id: Optional[int] = None
            other_id: int
            other: ClassVar[AsyncBelongsTo["AsyncOther"]] = AsyncBelongsTo(
                foreign_key="other_id", inverse_of="item"
            )

        rel = AsyncItem.get_relation("other")
        with pytest.raises(ValueError, match="Invalid relationship pair"):
            rel.get_related_model(AsyncItem)

    def test_async_missing_inverse_raises(self):
        """Missing inverse should raise ValueError."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncRelated(AsyncActiveRecord):
            __table_name__ = "v_mi_rel"
            id: Optional[int] = None
            owner_id: int

        class AsyncOwner(AsyncActiveRecord):
            __table_name__ = "v_mi_own"
            id: Optional[int] = None
            items: ClassVar[AsyncHasMany["AsyncRelated"]] = AsyncHasMany(
                foreign_key="owner_id", inverse_of="nonexistent"
            )

        rel = AsyncOwner.get_relation("items")
        with pytest.raises(ValueError, match="not found"):
            rel.get_related_model(AsyncOwner)

    def test_async_auto_set_inverse_of(self):
        """Validator should auto-set inverse_of when missing."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncRelated(AsyncActiveRecord):
            __table_name__ = "v_asi_rel"
            id: Optional[int] = None
            owner_id: int
            owner: ClassVar[AsyncBelongsTo["AsyncOwner"]] = AsyncBelongsTo(
                foreign_key="owner_id"
            )

        class AsyncOwner(AsyncActiveRecord):
            __table_name__ = "v_asi_own"
            id: Optional[int] = None
            items: ClassVar[AsyncHasMany["AsyncRelated"]] = AsyncHasMany(
                foreign_key="owner_id", inverse_of="owner"
            )

        rel = AsyncOwner.get_relation("items")
        rel.get_related_model(AsyncOwner)
        related_rel = AsyncRelated.get_relation("owner")
        assert related_rel.inverse_of == "items"


