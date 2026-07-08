# src/rhosocial/activerecord/testsuite/feature/mixins/test_timestamps_async.py
"""
Test timestamp functionality
"""
import pytest

import asyncio
from datetime import datetime


@pytest.mark.asyncio


async def test_timestamps(async_timestamped_post_model):
    """Test timestamp functionality"""
    # Create new record
    post = async_timestamped_post_model(title="Test AsyncPost", content="Test Content")
    await post.save()

    # Verify timestamps exist and have correct type
    assert post.created_at is not None
    assert post.updated_at is not None
    assert isinstance(post.created_at, datetime)
    assert isinstance(post.updated_at, datetime)

    # Record initial timestamps
    original_created_at = post.created_at
    original_updated_at = post.updated_at

    # Wait a moment then update the record
    post.title = "Updated Title"
    await asyncio.sleep(0.1)
    await post.save()

    # Verify timestamp updates
    assert post.created_at == original_created_at  # Creation time unchanged
    assert post.updated_at > original_updated_at  # Update time changed


@pytest.mark.asyncio


async def test_timestamps_set_both_on_insert(async_timestamped_post_model):
    """Test that BEFORE_INSERT sets both created_at and updated_at to the same value.

    This verifies the behavior of _set_timestamps_on_insert handler:
    - Both timestamps should be set to the same value on INSERT
    - This ensures consistency for new records
    """
    # Create new record
    post = async_timestamped_post_model(title="New AsyncPost", content="Content")
    await post.save()

    # Verify both timestamps are set and equal for new records
    assert post.created_at is not None
    assert post.updated_at is not None
    # Both timestamps should be exactly the same on INSERT
    assert post.created_at == post.updated_at, (
        "created_at and updated_at should be equal on INSERT"
    )


@pytest.mark.asyncio


async def test_timestamps_only_updated_at_changes_on_update(async_timestamped_post_model):
    """Test that BEFORE_UPDATE only modifies updated_at, not created_at.

    This verifies the separation of INSERT and UPDATE event handlers:
    - BEFORE_INSERT sets both created_at and updated_at
    - BEFORE_UPDATE only modifies updated_at
    """
    # Create new record
    post = async_timestamped_post_model(title="Original Title", content="Original Content")
    await post.save()

    original_created_at = post.created_at
    original_updated_at = post.updated_at

    # Verify initial state
    assert original_created_at == original_updated_at

    # Wait a moment then update
    await asyncio.sleep(0.1)
    post.title = "Updated Title"
    await post.save()

    # created_at should remain unchanged
    assert post.created_at == original_created_at, (
        "created_at should not change on UPDATE"
    )

    # updated_at should be different
    assert post.updated_at > original_updated_at, (
        "updated_at should be updated on UPDATE"
    )