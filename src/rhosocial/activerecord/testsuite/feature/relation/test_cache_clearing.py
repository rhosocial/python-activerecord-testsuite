# src/rhosocial/activerecord/testsuite/feature/relation/test_cache_clearing.py
"""
Tests for relation cache clearing via descriptor __delete__.

`del instance.relation` clears the cached query result for that instance,
causing the next access to trigger a fresh load from the loader.
"""
import pytest


class TestCacheClearing:
    """Sync tests for clearing relation cache via `del instance.relation`."""

    def test_del_clears_belongs_to_cache(self, book):
        """del instance.relation clears BelongsTo cache; next access reloads."""
        author1 = book.author()
        assert author1 is not None
        assert author1.name == "Test Author"

        del book.author

        author2 = book.author()
        assert author2 is not None
        assert author2.name == "Test Author"
        assert author2 is not author1

    def test_del_clears_has_many_cache(self, author):
        """del instance.relation clears HasMany cache; next access reloads."""
        books1 = author.books()
        assert len(books1) == 1

        del author.books

        books2 = author.books()
        assert len(books2) == 1
        assert books2 is not books1

    def test_del_clears_has_one_cache(self, author):
        """del instance.relation clears HasOne cache; next access reloads."""
        profile1 = author.profile()
        assert profile1 is not None

        del author.profile

        profile2 = author.profile()
        assert profile2 is not None
        assert profile2 is not profile1

    def test_cache_is_per_instance(self, book):
        """Each instance maintains its own cache; del affects only the target."""
        from rhosocial.activerecord.testsuite.feature.relation.conftest import Book

        book2 = Book(id=2, title="Another Book", author_id=2)

        author_a = book.author()
        author_b = book2.author()

        del book.author

        author_a2 = book.author()
        author_b2 = book2.author()

        assert author_a2 is not author_a
        assert author_b2 is author_b


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
