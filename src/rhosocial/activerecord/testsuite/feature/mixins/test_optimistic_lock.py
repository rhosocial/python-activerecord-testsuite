# src/rhosocial/activerecord/testsuite/feature/mixins/test_optimistic_lock.py
"""
Test optimistic locking functionality
"""
import pytest

from rhosocial.activerecord.backend.errors import (
    DatabaseError,
    IntegrityError,
    StaleRecordError,
)
from rhosocial.activerecord.backend.options import UpdateOptions


def test_optimistic_lock(versioned_product_model):
    """Test optimistic locking functionality"""
    # Create new record
    product = versioned_product_model(name="Test Product", price=10.0)
    product.save()

    # Verify initial version
    assert product.version == 1

    # Update record
    product.price = 15.0
    product.save()

    # Verify version increment
    assert product.version == 2

    # Simulate concurrent update conflict
    product_conflict = versioned_product_model.find_one(product.id)
    product_conflict.price = 20.0
    product_conflict.save()  # This update succeeds, version becomes 3

    # Original record update should now fail
    product.price = 25.0  # product.version is still 2 here
    with pytest.raises(
        StaleRecordError, match="Record was updated by another process"
    ) as exc_info:
        product.save()

    stale = exc_info.value
    assert stale.model is versioned_product_model
    assert stale.primary_key == product.id
    assert stale.expected_version == 2
    assert stale.operation == "update"

    # Verify final version
    latest_product = versioned_product_model.find_one(product.id)
    assert latest_product.version == 3
    assert latest_product.price == pytest.approx(20.0)


def test_stale_record_error_is_database_error(versioned_product_model):
    """A stale record remains catchable through the DatabaseError base class."""
    product = versioned_product_model(name="Test Product", price=10.0)
    product.save()

    product_conflict = versioned_product_model.find_one(product.id)
    product_conflict.price = 20.0
    product_conflict.save()

    product.price = 25.0
    with pytest.raises(
        DatabaseError, match="Record was updated by another process"
    ) as exc_info:
        product.save()

    # The concrete type is still available to callers that opt in.
    assert isinstance(exc_info.value, StaleRecordError)


def test_integrity_error_is_not_stale(versioned_product_model):
    """A plain database constraint failure keeps its own type."""
    product = versioned_product_model(name="Test Product", price=10.0)
    product.save()

    # Update through the backend without the optimistic-lock condition, and
    # violate the NOT NULL constraint. This is a plain database error, not a
    # stale-record conflict.
    where = versioned_product_model._build_pk_where_predicate(product._get_pk_value())
    with pytest.raises(IntegrityError) as exc_info:
        product.backend().update(
            UpdateOptions(
                table=product.table_name(),
                data={"name": None},
                where=where,
            )
        )

    assert not isinstance(exc_info.value, StaleRecordError)


def test_version_increment(versioned_product_model):
    """Test version number increments correctly"""
    # Create new record
    product = versioned_product_model(name="Test Product", price=10.0)
    product.save()

    # Verify initial version
    assert product.version == 1

    # First update
    product.price = 15.0
    product.save()
    assert product.version == 2

    # Second update
    product.price = 20.0
    product.save()
    assert product.version == 3

    # Verify version in database
    db_product = versioned_product_model.find_one(product.id)
    assert db_product.version == 3


def test_version_initializes_to_one_on_insert(versioned_product_model):
    """Test that AFTER_INSERT ensures version is initialized to 1.

    This verifies the behavior of _handle_version_after_insert handler:
    - New records should have version = 1 after INSERT
    - This is handled by the AFTER_INSERT event, not just default value
    """
    # Create new record
    product = versioned_product_model(name="New Product", price=99.99)
    product.save()

    # Verify version is initialized to 1
    assert product.version == 1, (
        "Version should be initialized to 1 on INSERT"
    )

    # Verify in database
    db_product = versioned_product_model.find_one(product.id)
    assert db_product.version == 1, (
        "Version in database should be 1 after INSERT"
    )


def test_version_events_separation(versioned_product_model):
    """Test that INSERT and UPDATE use separate event handlers.

    This verifies:
    - AFTER_INSERT initializes version for new records
    - AFTER_UPDATE handles version increment and conflict detection
    """
    # INSERT: version initialized to 1
    product = versioned_product_model(name="Test Product", price=50.0)
    product.save()
    assert product.version == 1

    # UPDATE 1: version incremented to 2
    product.price = 60.0
    product.save()
    assert product.version == 2

    # UPDATE 2: version incremented to 3
    product.price = 70.0
    product.save()
    assert product.version == 3

    # Verify that the version field is properly managed
    # by separate INSERT/UPDATE handlers
    db_product = versioned_product_model.find_one(product.id)
    assert db_product.version == 3