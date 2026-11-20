# src/rhosocial/activerecord/testsuite/feature/query/basic/test_find_one_or_create_async.py
"""Contract tests for ``find_one_or_create`` with a natural key, asynchronously."""
from decimal import Decimal

import pytest

from rhosocial.activerecord.backend.errors import IntegrityError


async def test_creates_with_lookup_and_defaults(async_order_fixtures):
    """A missing natural key is inserted with lookup and defaults values."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username="foc_user", email="foc@example.com", age=30)
    await user.save()

    row, created = await AsyncOrder.find_one_or_create(
        user_id=user.id,
        order_number="FOC-001",
        defaults={"total_amount": Decimal("12.34"), "status": "processing"},
    )

    assert created is True
    assert row.id is not None
    assert row.order_number == "FOC-001"
    assert row.total_amount == Decimal("12.34")
    assert row.status == "processing"
    assert await AsyncOrder.query().where("order_number = ?", ("FOC-001",)).count() == 1


async def test_returns_existing_and_ignores_defaults(async_order_fixtures):
    """An existing row is returned untouched; defaults are creation-only."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username="foc_existing", email="foc_existing@example.com", age=30)
    await user.save()

    first, created = await AsyncOrder.find_one_or_create(
        user_id=user.id,
        order_number="FOC-002",
        defaults={"status": "processing", "total_amount": Decimal("10.00")},
    )
    assert created is True

    second, created = await AsyncOrder.find_one_or_create(
        user_id=user.id,
        order_number="FOC-002",
        defaults={"status": "done", "total_amount": Decimal("99.00")},
    )

    assert created is False
    assert second.id == first.id
    assert second.status == "processing", "defaults must not update an existing row"
    assert second.total_amount == Decimal("10.00")
    assert await AsyncOrder.query().where("order_number = ?", ("FOC-002",)).count() == 1


async def test_lookup_wins_over_defaults(async_order_fixtures):
    """The lookup value defines the identity even when defaults name the same field."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username="foc_winner", email="foc_winner@example.com", age=30)
    await user.save()

    row, created = await AsyncOrder.find_one_or_create(
        user_id=user.id,
        order_number="FOC-003",
        defaults={"order_number": "IGNORED"},
    )

    assert created is True
    assert row.order_number == "FOC-003"


async def test_empty_lookup_is_rejected(async_order_fixtures):
    """An empty natural key must not return an arbitrary row."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    with pytest.raises(ValueError, match="at least one lookup field"):
        await AsyncOrder.find_one_or_create()


async def test_unknown_lookup_field_is_rejected(async_order_fixtures):
    """Lookup keys must be model fields."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    with pytest.raises(TypeError, match="not a field"):
        await AsyncOrder.find_one_or_create(nope=1)


async def test_generated_primary_key_lookup_is_rejected(async_order_fixtures):
    """A database-generated primary key cannot identify the row to create."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    with pytest.raises(ValueError, match="generates its primary key"):
        await AsyncOrder.find_one_or_create(id=1)


async def test_natural_key_on_composite_pk_model(async_order_item_class):
    """Non-primary-key lookup works on a composite-PK model too."""
    row, created = await async_order_item_class.find_one_or_create(
        quantity=2,
        defaults={
            "order_id": 3,
            "product_id": 103,
            "unit_price": Decimal("5.00"),
        },
    )

    assert created is True
    assert row.order_id == 3
    assert row.product_id == 103

    same, created = await async_order_item_class.find_one_or_create(
        quantity=2,
        defaults={
            "order_id": 4,
            "product_id": 104,
            "unit_price": Decimal("6.00"),
        },
    )

    assert created is False
    assert same.order_id == 3, "the existing composite row is returned"
    assert same.product_id == 103


async def test_conflict_without_matching_lookup_reraises(async_order_item_class):
    """A primary-key collision that the lookup cannot explain is re-raised."""
    existing = async_order_item_class(
        order_id=1,
        product_id=101,
        quantity=1,
        unit_price=Decimal("1.00"),
    )
    await existing.save()

    with pytest.raises(IntegrityError):
        await async_order_item_class.find_one_or_create(
            quantity=999,
            defaults={"order_id": 1, "product_id": 101, "unit_price": Decimal("1.00")},
        )
