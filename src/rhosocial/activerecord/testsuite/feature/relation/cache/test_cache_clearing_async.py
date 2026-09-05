# src/rhosocial/activerecord/testsuite/feature/relation/cache/test_cache_clearing_async.py
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
        assert author1 is not None, "Expected the related author to be loaded"
        assert author1.name == "Test Author", "Expected the author name to be 'Test Author'"

        del async_book.author

        author2 = await async_book.author()
        assert author2 is not None, "Expected the related author to be reloaded"
        assert author2.name == "Test Author", "Expected the reloaded author name to match"
        assert author2 is not author1, "Expected a fresh instance after cache clear"

    async def test_del_clears_has_many_cache(self, async_author):
        """del instance.relation clears HasMany cache; next access reloads."""
        books1 = await async_author.books()
        assert len(books1) == 1, "Expected 1 book in the cached result"

        del async_author.books

        books2 = await async_author.books()
        assert len(books2) == 1, "Expected 1 book after reload"
        assert books2 is not books1, "Expected a fresh list after cache clear"

    async def test_del_clears_has_one_cache(self, async_author):
        """del instance.relation clears HasOne cache; next access reloads."""
        profile1 = await async_author.profile()
        assert profile1 is not None, "Expected the related profile to be loaded"

        del async_author.profile

        profile2 = await async_author.profile()
        assert profile2 is not None, "Expected the related profile to be reloaded"
        assert profile2 is not profile1, "Expected a fresh profile after cache clear"

    async def test_cache_is_per_instance(self, async_book):
        """Each instance maintains its own cache; del affects only the target."""
        from rhosocial.activerecord.testsuite.feature.relation.conftest import AsyncBook

        book2 = AsyncBook(id=2, title="Another Book", author_id=2)

        author_a = await async_book.author()
        author_b = await book2.author()

        del async_book.author

        author_a2 = await async_book.author()
        author_b2 = await book2.author()

        assert author_a2 is not author_a, "Expected async_book cache to be cleared"
        assert author_b2 is author_b, "Expected book2 cache to remain intact"
