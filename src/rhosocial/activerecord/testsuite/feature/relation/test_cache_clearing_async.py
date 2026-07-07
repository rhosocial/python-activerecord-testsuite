# src/rhosocial/activerecord/testsuite/feature/relation/test_cache_clearing.py
"""
Tests for relation cache clearing via descriptor __delete__.

`del instance.relation` clears the cached query result for that instance,
causing the next access to trigger a fresh load from the loader.
"""
import pytest
class TestAsyncCacheClearing:
    """Async tests for clearing relation cache via `del instance.relation`."""

    @pytest.mark.asyncio
    async def test_del_clears_async_belongs_to_cache(self, async_user_post_comment_classes):
        """del clears async BelongsTo cache; next access reloads."""
        user_class, post_class, comment_class = async_user_post_comment_classes

        user = user_class(name="Alice", email="alice@example.com")
        await user.save()

        post = post_class(title="Hello", body="Content", user_id=user.id)
        await post.save()

        loaded_user1 = await post.user()
        assert loaded_user1 is not None
        assert loaded_user1.id == user.id

        del post.user

        loaded_user2 = await post.user()
        assert loaded_user2 is not None
        assert loaded_user2.id == user.id
        assert loaded_user2 is not loaded_user1

    @pytest.mark.asyncio
    async def test_del_clears_async_has_many_cache(self, async_user_post_comment_classes):
        """del clears async HasMany cache; next access reloads."""
        user_class, post_class, comment_class = async_user_post_comment_classes

        user = user_class(name="Bob", email="bob@example.com")
        await user.save()

        post = post_class(title="Post1", body="Body", user_id=user.id)
        await post.save()

        posts1 = await user.posts()
        assert len(posts1) == 1

        del user.posts

        posts2 = await user.posts()
        assert len(posts2) == 1
        assert posts2 is not posts1

    @pytest.mark.asyncio
    async def test_async_cache_is_per_instance(self, async_user_post_comment_classes):
        """Each async instance maintains its own cache; del affects only the target."""
        user_class, post_class, comment_class = async_user_post_comment_classes

        user1 = user_class(name="User1", email="u1@example.com")
        await user1.save()
        user2 = user_class(name="User2", email="u2@example.com")
        await user2.save()

        post1 = post_class(title="P1", body="B1", user_id=user1.id)
        await post1.save()
        post2 = post_class(title="P2", body="B2", user_id=user2.id)
        await post2.save()

        loaded_user1_a = await post1.user()
        loaded_user2_a = await post2.user()

        del post1.user

        loaded_user1_b = await post1.user()
        loaded_user2_b = await post2.user()

        assert loaded_user1_b is not loaded_user1_a
        assert loaded_user2_b is loaded_user2_a

    @pytest.mark.asyncio
    async def test_del_clears_async_has_one_cache(self, async_user_post_comment_classes):
        """del clears async HasOne cache; next access reloads."""
        from rhosocial.activerecord.testsuite.feature.relation.fixtures.models import AsyncBoundaryOwner, AsyncBoundaryProfile

        owner = AsyncBoundaryOwner(name="Owner1")
        await owner.save()

        profile = AsyncBoundaryProfile(bio="Bio1", owner_id=owner.id)
        await profile.save()

        loaded1 = await owner.profile()
        assert loaded1 is not None
        assert loaded1.bio == "Bio1"

        del owner.profile

        loaded2 = await owner.profile()
        assert loaded2 is not None
        assert loaded2.bio == "Bio1"
        assert loaded2 is not loaded1