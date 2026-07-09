# src/rhosocial/activerecord/testsuite/feature/relation/test_descriptors_async.py
"""
Async tests for relation descriptor functionality.
Mirrors test_descriptors.py for sync/async parity.

Tests AsyncBelongsTo/AsyncHasOne/AsyncHasMany descriptor types:
initialization, default loader, custom cache config, type validation,
and correct registration on AsyncActiveRecord subclasses.
"""
import pytest
from typing import ClassVar, Optional

from rhosocial.activerecord.relation.base import RelationManagementMixin
from rhosocial.activerecord.relation.descriptors import BelongsTo, HasOne, HasMany
from rhosocial.activerecord.relation.async_descriptors import (
    AsyncBelongsTo, AsyncHasOne, AsyncHasMany, AsyncRelationDescriptor
)
from rhosocial.activerecord.relation.cache import CacheConfig


class TestAsyncRelationDescriptors:
    """Async tests for relation descriptor functionality.

    Mirrors test_descriptors.py for sync/async parity.

    Tests AsyncBelongsTo/AsyncHasOne/AsyncHasMany descriptor types:
    initialization, default loader, custom cache config, type validation,
    and correct registration on AsyncActiveRecord subclasses.
    """

    async def test_belongs_to_relation(self):
        """AsyncBelongsTo stores foreign_key and inverse_of and is an AsyncRelationDescriptor."""
        desc = AsyncBelongsTo(foreign_key="user_id", inverse_of="posts")
        assert isinstance(desc, AsyncRelationDescriptor)
        assert desc.foreign_key == "user_id"
        assert desc.inverse_of == "posts"

    async def test_has_many_relation(self):
        """AsyncHasMany stores foreign_key and inverse_of and is an AsyncRelationDescriptor."""
        desc = AsyncHasMany(foreign_key="user_id", inverse_of="user")
        assert isinstance(desc, AsyncRelationDescriptor)
        assert desc.foreign_key == "user_id"
        assert desc.inverse_of == "user"

    async def test_has_one_relation(self):
        """AsyncHasOne stores foreign_key and inverse_of and is an AsyncRelationDescriptor."""
        desc = AsyncHasOne(foreign_key="author_id", inverse_of="author")
        assert isinstance(desc, AsyncRelationDescriptor)
        assert desc.foreign_key == "author_id"
        assert desc.inverse_of == "author"

    # ── async descriptors on AsyncActiveRecord models ─────────────────

    async def test_belongs_to_on_model(self):
        """AsyncBelongsTo on AsyncActiveRecord registers without error."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncPost(AsyncActiveRecord):
            __table_name__ = "desc_ab_post"
            id: Optional[int] = None
            user_id: int
            user: ClassVar[AsyncBelongsTo["AsyncUser"]] = AsyncBelongsTo(
                foreign_key="user_id", inverse_of=None
            )

        assert hasattr(AsyncPost, "user")
        assert AsyncPost.get_relation("user") is not None
        assert isinstance(AsyncPost.get_relation("user"), AsyncBelongsTo)

    async def test_has_many_on_model(self):
        """AsyncHasMany on AsyncActiveRecord registers without error."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncUser(AsyncActiveRecord):
            __table_name__ = "desc_hm_user"
            id: Optional[int] = None
            posts: ClassVar[AsyncHasMany["AsyncPost"]] = AsyncHasMany(
                foreign_key="user_id", inverse_of=None
            )

        assert hasattr(AsyncUser, "posts")
        assert AsyncUser.get_relation("posts") is not None
        assert isinstance(AsyncUser.get_relation("posts"), AsyncHasMany)

    async def test_has_one_on_model(self):
        """AsyncHasOne on AsyncActiveRecord registers without error."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncUser(AsyncActiveRecord):
            __table_name__ = "desc_ho_user"
            id: Optional[int] = None
            profile: ClassVar[AsyncHasOne["AsyncProfile"]] = AsyncHasOne(
                foreign_key="user_id", inverse_of=None
            )

        assert hasattr(AsyncUser, "profile")
        assert AsyncUser.get_relation("profile") is not None
        assert isinstance(AsyncUser.get_relation("profile"), AsyncHasOne)

    async def test_query_method_created(self):
        """Descriptor __set_name__ creates {name}_query method on the owner class."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        class AsyncUser(AsyncActiveRecord):
            __table_name__ = "desc_qm_user"
            id: Optional[int] = None
            posts: ClassVar[AsyncHasMany["AsyncPost"]] = AsyncHasMany(
                foreign_key="user_id", inverse_of=None
            )

        assert hasattr(AsyncUser, "posts_query")

    async def test_descriptor_default_loader(self):
        """When no loader is supplied, the descriptor creates AsyncDefaultRelationLoader."""
        desc = AsyncBelongsTo(foreign_key="user_id")
        from rhosocial.activerecord.relation.async_descriptors import AsyncDefaultRelationLoader
        assert isinstance(desc._loader, AsyncDefaultRelationLoader)

    async def test_descriptor_custom_cache_config(self):
        """Custom CacheConfig (disabled, ttl=60, max_size=10) is stored correctly."""
        config = CacheConfig(enabled=False, ttl=60, max_size=10)
        desc = AsyncBelongsTo(foreign_key="user_id", cache_config=config)
        assert desc._cache_config is config
        assert desc._cache_config.enabled is False
        assert desc._cache_config.ttl == 60
        assert desc._cache_config.max_size == 10

    async def test_descriptor_default_cache_config(self):
        """No cache_config supplied -> default CacheConfig (enabled=True, ttl=300, max_size=1000)."""
        desc = AsyncBelongsTo(foreign_key="user_id")
        assert desc._cache_config.enabled is True
        assert desc._cache_config.ttl == 300
        assert desc._cache_config.max_size == 1000

    async def test_descriptor_foreign_key_type_error(self):
        """Passing a non-string foreign_key raises TypeError."""
        with pytest.raises(TypeError, match="foreign_key must be a string"):
            AsyncBelongsTo(foreign_key=123)

    async def test_descriptor_cache_config_type_error(self):
        """Passing a non-CacheConfig object raises TypeError."""
        with pytest.raises(TypeError, match="cache_config must be instance of CacheConfig"):
            AsyncBelongsTo(foreign_key="user_id", cache_config="invalid")









