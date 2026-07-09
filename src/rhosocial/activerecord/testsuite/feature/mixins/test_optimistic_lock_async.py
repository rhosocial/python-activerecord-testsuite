# src/rhosocial/activerecord/testsuite/feature/mixins/test_optimistic_lock_async.py
"""
Test optimistic locking functionality
"""
import pytest

from rhosocial.activerecord.backend.errors import DatabaseError


async def test_optimistic_lock(async_versioned_product_model):
    """Test optimistic locking functionality"""
    # Create new record
    product = async_versioned_product_model(name="Test Product", price=10.0)
    await product.save()

    # Verify initial version
    assert product.version == 1

    # Update record
    product.price = 15.0
    await product.save()

    # Verify version increment
    assert product.version == 2

    # Simulate concurrent update conflict
    product_conflict = await async_versioned_product_model.find_one(product.id)
    product_conflict.price = 20.0
    await product_conflict.save()  # This update succeeds, version becomes 3

    # Original record update should now fail
    product.price = 25.0  # product.version is still 2 here
    with pytest.raises(DatabaseError, match="Record was updated by another process"):
        await product.save()

    # Verify final version
    latest_product = await async_versioned_product_model.find_one(product.id)
    assert latest_product.version == 3
    assert latest_product.price == pytest.approx(20.0)


async def test_version_increment(async_versioned_product_model):
    """Test version number increments correctly"""
    # Create new record
    product = async_versioned_product_model(name="Test Product", price=10.0)
    await product.save()

    # Verify initial version
    assert product.version == 1

    # First update
    product.price = 15.0
    await product.save()
    assert product.version == 2

    # Second update
    product.price = 20.0
    await product.save()
    assert product.version == 3

    # Verify version in database
    db_product = await async_versioned_product_model.find_one(product.id)
    assert db_product.version == 3


async def test_version_initializes_to_one_on_insert(async_versioned_product_model):
    """Test that AFTER_INSERT ensures version is initialized to 1.

    This verifies the behavior of _handle_version_after_insert handler:
    - New records should have version = 1 after INSERT
    - This is handled by the AFTER_INSERT event, not just default value
    """
    # Create new record
    product = async_versioned_product_model(name="New Product", price=99.99)
    await product.save()

    # Verify version is initialized to 1
    assert product.version == 1, (
        "Version should be initialized to 1 on INSERT"
    )

    # Verify in database
    db_product = await async_versioned_product_model.find_one(product.id)
    assert db_product.version == 1, (
        "Version in database should be 1 after INSERT"
    )


async def test_version_events_separation(async_versioned_product_model):
    """Test that INSERT and UPDATE use separate event handlers.

    This verifies:
    - AFTER_INSERT initializes version for new records
    - AFTER_UPDATE handles version increment and conflict detection
    """
    # INSERT: version initialized to 1
    product = async_versioned_product_model(name="Test Product", price=50.0)
    await product.save()
    assert product.version == 1

    # UPDATE 1: version incremented to 2
    product.price = 60.0
    await product.save()
    assert product.version == 2

    # UPDATE 2: version incremented to 3
    product.price = 70.0
    await product.save()
    assert product.version == 3

    # Verify that the version field is properly managed
    # by separate INSERT/UPDATE handlers
    db_product = await async_versioned_product_model.find_one(product.id)
    assert db_product.version == 3