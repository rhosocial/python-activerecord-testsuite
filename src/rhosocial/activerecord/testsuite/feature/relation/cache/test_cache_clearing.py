# src/rhosocial/activerecord/testsuite/feature/relation/cache/test_cache_clearing.py
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
        assert author1 is not None, "Expected the related author to be loaded"
        assert author1.name == "Test Author", "Expected the author name to be 'Test Author'"

        del book.author

        author2 = book.author()
        assert author2 is not None, "Expected the related author to be reloaded"
        assert author2.name == "Test Author", "Expected the reloaded author name to match"
        assert author2 is not author1, "Expected a fresh instance after cache clear"

    def test_del_clears_has_many_cache(self, author):
        """del instance.relation clears HasMany cache; next access reloads."""
        books1 = author.books()
        assert len(books1) == 1, "Expected 1 book in the cached result"

        del author.books

        books2 = author.books()
        assert len(books2) == 1, "Expected 1 book after reload"
        assert books2 is not books1, "Expected a fresh list after cache clear"

    def test_del_clears_has_one_cache(self, author):
        """del instance.relation clears HasOne cache; next access reloads."""
        profile1 = author.profile()
        assert profile1 is not None, "Expected the related profile to be loaded"

        del author.profile

        profile2 = author.profile()
        assert profile2 is not None, "Expected the related profile to be reloaded"
        assert profile2 is not profile1, "Expected a fresh profile after cache clear"

    def test_cache_is_per_instance(self, book):
        """Each instance maintains its own cache; del affects only the target."""
        from rhosocial.activerecord.testsuite.feature.relation.conftest import Book

        book2 = Book(id=2, title="Another Book", author_id=2)

        author_a = book.author()
        author_b = book2.author()

        del book.author

        author_a2 = book.author()
        author_b2 = book2.author()

        assert author_a2 is not author_a, "Expected book cache to be cleared"
        assert author_b2 is author_b, "Expected book2 cache to remain intact"