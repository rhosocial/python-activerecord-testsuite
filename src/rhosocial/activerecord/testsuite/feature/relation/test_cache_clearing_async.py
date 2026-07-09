# src/rhosocial/activerecord/testsuite/feature/relation/test_cache_clearing_async.py
"""
Tests for relation cache clearing via descriptor __delete__.

`del instance.relation` clears the cached query result for that instance,
causing the next access to trigger a fresh load from the loader.
"""
class TestAsyncCacheClearing:
    """Async tests for clearing relation cache via `del instance.relation`."""

    async def test_del_clears_belongs_to_cache(self, async_book):
        """del instance.relation clears BelongsTo cache; next access reloads."""
        author1 = await async_book.author()
        assert author1 is not None
        assert author1.name == "Test Author"

        del async_book.author

        author2 = await async_book.author()
        assert author2 is not None
        assert author2.name == "Test Author"
        assert author2 is not author1

    async def test_del_clears_has_many_cache(self, async_author):
        """del instance.relation clears HasMany cache; next access reloads."""
        books1 = await async_author.books()
        assert len(books1) == 1

        del async_author.books

        books2 = await async_author.books()
        assert len(books2) == 1
        assert books2 is not books1

    async def test_del_clears_has_one_cache(self, async_author):
        """del instance.relation clears HasOne cache; next access reloads."""
        profile1 = await async_author.profile()
        assert profile1 is not None

        del async_author.profile

        profile2 = await async_author.profile()
        assert profile2 is not None
        assert profile2 is not profile1

    async def test_cache_is_per_instance(self, async_book):
        """Each instance maintains its own cache; del affects only the target."""
        from rhosocial.activerecord.testsuite.feature.relation.conftest import AsyncBook

        book2 = AsyncBook(id=2, title="Another Book", author_id=2)

        author_a = await async_book.author()
        author_b = await book2.author()

        del async_book.author

        author_a2 = await async_book.author()
        author_b2 = await book2.author()

        assert author_a2 is not author_a
        assert author_b2 is author_b
