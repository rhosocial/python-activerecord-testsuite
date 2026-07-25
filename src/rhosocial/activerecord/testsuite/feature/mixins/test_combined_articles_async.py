# src/rhosocial/activerecord/testsuite/feature/mixins/test_combined_articles_async.py
"""
Test combined functionality
"""
import asyncio

import pytest

from rhosocial.activerecord.backend.errors import DatabaseError
from rhosocial.activerecord.testsuite.utils import assert_datetime_equal


async def test_combined_update(async_combined_article_model):
    """Test combined functionality when updating records"""
    # Create and update article
    article = async_combined_article_model(title="Test", content="Test")
    await article.save()
    original_updated_at = article.updated_at

    article.content = "Updated content"
    article.status = "published"
    await asyncio.sleep(0.1)
    await article.save()

    # Verify updated state
    assert article.version == 2  # Version number increments
    assert_datetime_equal(article.created_at, original_updated_at)  # Creation time remains unchanged
    assert article.updated_at > original_updated_at  # Update time changes


async def test_combined_delete(async_combined_article_model):
    """Test combined functionality when deleting records"""
    # Create and delete article
    article = async_combined_article_model(title="Test", content="Test")
    await article.save()
    await article.delete()

    # Verify soft delete status
    assert article.deleted_at is not None
    assert await async_combined_article_model.find_one(article.id) is None

    # Verify deleted records can be found
    found_article = await async_combined_article_model.query_with_deleted().where(
        f"{async_combined_article_model.primary_key()} = ?",
        (article.id,)
    ).one()
    assert found_article is not None
    assert found_article.deleted_at is not None
    assert found_article.version == 1


async def test_combined_concurrent_update(async_combined_article_model):
    """Test combined functionality during concurrent updates"""
    # Create article
    article = async_combined_article_model(title="Test", content="Test")
    await article.save()

    # Simulate concurrent updates
    concurrent_article = await async_combined_article_model.query_with_deleted().where(
        f"{async_combined_article_model.primary_key()} = ?",
        (article.id,)
    ).one()

    # First update succeeds
    article.content = "Updated by first"
    await article.save()

    # Second update fails
    concurrent_article.content = "Updated by second"
    with pytest.raises(DatabaseError, match="Record was updated by another process"):
        await concurrent_article.save()

    # Verify final state
    final_article = await async_combined_article_model.find_one(article.id)
    assert final_article.content == "Updated by first"
    assert final_article.version == 2
