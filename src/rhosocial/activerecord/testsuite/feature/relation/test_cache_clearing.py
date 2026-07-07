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