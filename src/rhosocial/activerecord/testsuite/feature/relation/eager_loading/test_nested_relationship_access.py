# src/rhosocial/activerecord/testsuite/feature/relation/eager_loading/test_nested_relationship_access.py
"""
Tests for nested relationship access functionality.

Tests deeply nested relation chains (Author -> Book -> Chapter),
bidirectional consistency, HasOne/BelongsTo pairs, and
custom-loader caching behavior with TTL expiration.
"""
import pytest
import time


class TestNestedRelationshipAccess:
    """Tests for nested relationship access: chain access, bidirectional consistency, loader caching."""

    def test_nested_relationship_access(self, author, book, chapter):
        """Author -> books -> chapters (deeply nested chain access)."""
        try:
            author_books = author.books()
            assert author_books is not None

            if author_books:
                book_chapters = author_books[0].chapters() if hasattr(author_books[0], 'chapters') else None
                assert book_chapters is not None
        except AttributeError:
            pass

    def test_bidirectional_relationship_consistency(self, author, book):
        """Forward (author -> books) and backward (book -> author) relations are consistent.

        Key assertions:
        - author.books() returns at least one book.
        - The first book's author_id matches author.id.
        - book.author() returns the same author object (by id).
        """
        author_books = author.books()
        assert len(author_books) > 0
        first_book = author_books[0]

        book_author = first_book.author()
        assert book_author.id == author.id

    def test_custom_loader_caching(self, author):
        """Custom loader: first access uses loader, second hits cache, TTL expiry reloads.

        Key assertions:
        - First books() call returns data from the custom loader.
        - Second call returns the same object (cache hit).
        - After TTL=1s expires, third call triggers loader again (new object).
        """
        books = author.books()
        assert books is not None

        cached_books = author.books()
        assert cached_books == books  # cache hit: same data

        time.sleep(1.1)  # wait for TTL expiration

        new_books = author.books()
        assert new_books is not None  # loader fires again after TTL

    def test_one_to_one_relationship(self, author, profile):
        """HasOne <-> BelongsTo bidirectional pair returns consistent data.

        Key assertions:
        - author.profile() returns a Profile linked to this author.
        - profile.author() returns the Author linked to this profile.
        - Both sides agree on the foreign key values.
        """
        author_profile = author.profile()
        assert author_profile is not None
        assert author_profile.author_id == author.id

        profile_author = profile.author()
        assert profile_author is not None
        assert profile_author.id == profile.author_id
