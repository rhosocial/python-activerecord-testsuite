# src/rhosocial/activerecord/testsuite/feature/mixins/test_timestamps.py
"""
Test timestamp functionality
"""
import time
from datetime import datetime, timedelta

from rhosocial.activerecord.testsuite.utils import assert_datetime_equal


def test_timestamps(timestamped_post_model):
    """Test timestamp functionality"""
    # Create new record
    post = timestamped_post_model(title="Test Post", content="Test Content")
    post.save()

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
    time.sleep(0.1)
    post.save()

    # Verify timestamp updates
    assert_datetime_equal(post.created_at, original_created_at)  # Creation time unchanged
    assert post.updated_at > original_updated_at  # Update time changed


def test_timestamps_set_both_on_insert(timestamped_post_model):
    """Test that BEFORE_INSERT sets both created_at and updated_at to the same value.

    This verifies the behavior of _set_timestamps_on_insert handler:
    - Both timestamps should be set to the same value on INSERT
    - This ensures consistency for new records
    """
    # Create new record
    post = timestamped_post_model(title="New Post", content="Content")
    post.save()

    # Verify both timestamps are set and equal for new records
    assert post.created_at is not None
    assert post.updated_at is not None
    # Both timestamps should be exactly the same on INSERT (strict tolerance:
    # these values come from the same Python datetime assignment, so no
    # database round-trip truncation can occur here).
    assert_datetime_equal(
        post.created_at, post.updated_at,
        tolerance=timedelta(seconds=0),
    )


def test_timestamps_only_updated_at_changes_on_update(timestamped_post_model):
    """Test that BEFORE_UPDATE only modifies updated_at, not created_at.

    This verifies the separation of INSERT and UPDATE event handlers:
    - BEFORE_INSERT sets both created_at and updated_at
    - BEFORE_UPDATE only modifies updated_at
    """
    # Create new record
    post = timestamped_post_model(title="Original Title", content="Original Content")
    post.save()

    original_created_at = post.created_at
    original_updated_at = post.updated_at

    # Verify initial state (strict equality: both come from the same INSERT
    # assignment, no database round-trip).
    assert_datetime_equal(
        original_created_at, original_updated_at,
        tolerance=timedelta(seconds=0),
    )

    # Wait a moment then update
    time.sleep(0.1)
    post.title = "Updated Title"
    post.save()

    # created_at should remain unchanged (strict equality for in-memory value).
    assert_datetime_equal(
        post.created_at, original_created_at,
        tolerance=timedelta(seconds=0),
    )

    # updated_at should be different
    assert post.updated_at > original_updated_at, (
        "updated_at should be updated on UPDATE"
    )