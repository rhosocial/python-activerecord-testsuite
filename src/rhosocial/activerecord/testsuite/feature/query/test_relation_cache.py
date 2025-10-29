# src/rhosocial/activerecord/testsuite/feature/query/test_relation_cache.py
"""Test cases for relation caching behavior."""
import random
import string
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import List

import pytest


@dataclass
class UserFixture:
    id: int
    username: str
    email: str
    age: int


@dataclass
class OrderFixture:
    id: int
    user_id: int
    order_number: str
    total_amount: Decimal


@dataclass
class OrderItemFixture:
    id: int
    order_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


@dataclass
class TestData:
    users: List[UserFixture]
    orders: List[OrderFixture]
    items: List[OrderItemFixture]


def generate_random_string(prefix: str, length: int = 8) -> str:
    """Generate random string with prefix"""
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}_{random_part}"


def generate_random_decimal(min_val: int = 10, max_val: int = 500) -> Decimal:
    """Generate random Decimal amount"""
    return Decimal(str(round(random.uniform(min_val, max_val), 2)))


def generate_random_quantity(min_val: int = 1, max_val: int = 10) -> int:
    """Generate random quantity"""
    return random.randint(min_val, max_val)


@pytest.fixture
def setup_order_data(order_fixtures) -> TestData:
    """Create random sample order data for testing."""
    User, Order, OrderItem = order_fixtures
    test_id = str(uuid.uuid4())[:8]  # Generate unique identifier for each test

    # Create test users
    users = []
    for i in range(2):
        username = generate_random_string(f"user{i}_{test_id}")
        email = f"{username}@example.com"
        age = random.randint(20, 60)

        user = User(username=username, email=email, age=age)
        user.save()

        users.append(UserFixture(
            id=user.id,
            username=username,
            email=email,
            age=age
        ))

    # Create orders for user
    orders = []
    # Two orders for user 1
    for i in range(2):
        order_number = generate_random_string(f"ORD{i}_{test_id}")
        total_amount = generate_random_decimal()

        order = Order(
            user_id=users[0].id,
            order_number=order_number,
            total_amount=total_amount
        )
        order.save()

        orders.append(OrderFixture(
            id=order.id,
            user_id=users[0].id,
            order_number=order_number,
            total_amount=total_amount
        ))

    # One empty order for user 2 (no order items)
    order_number = generate_random_string(f"ORD_EMPTY_{test_id}")
    total_amount = generate_random_decimal()

    order = Order(
        user_id=users[1].id,
        order_number=order_number,
        total_amount=total_amount
    )
    order.save()

    orders.append(OrderFixture(
        id=order.id,
        user_id=users[1].id,
        order_number=order_number,
        total_amount=total_amount
    ))

    # Create order items
    items = []

    # Create one order item for the first order
    product_name = generate_random_string("Product1")
    quantity = generate_random_quantity()
    unit_price = generate_random_decimal()
    subtotal = unit_price * quantity

    item = OrderItem(
        order_id=orders[0].id,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=subtotal
    )
    item.save()

    items.append(OrderItemFixture(
        id=item.id,
        order_id=orders[0].id,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=subtotal
    ))

    # Create one order item for the second order
    product_name = generate_random_string("Product2")
    quantity = generate_random_quantity()
    unit_price = generate_random_decimal()
    subtotal = unit_price * quantity

    item = OrderItem(
        order_id=orders[1].id,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=subtotal
    )
    item.save()

    items.append(OrderItemFixture(
        id=item.id,
        order_id=orders[1].id,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=subtotal
    ))

    # Return data class with all test data
    return TestData(users=users, orders=orders, items=items)





def test_basic_relation_caching(order_fixtures, setup_order_data):
    """Test basic relation caching behavior."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get the first order ID from test data
    order_id = test_data.orders[0].id
    expected_product_name = test_data.items[0].product_name

    # First query - should load from database
    order = Order.query().with_("items").where("id = ?", (order_id,)).one()

    assert order is not None
    assert len(order.items()) == 1
    assert order.items()[0].product_name == expected_product_name

    # Second query - should use cache
    order_again = Order.query().with_("items").where("id = ?", (order_id,)).one()

    assert order_again is not None
    assert len(order_again.items()) == 1
    assert order_again.items()[0].product_name == expected_product_name


def test_empty_relation_consistency(order_fixtures, setup_order_data):
    """Test that empty relations are correctly loaded and not affected by other queries."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get empty order ID (third order)
    empty_order_id = test_data.orders[2].id
    order_with_items_id = test_data.orders[0].id
    expected_product_name = test_data.items[0].product_name

    # First query - empty order should have no order items
    order3 = Order.query().with_("items").where("id = ?", (empty_order_id,)).one()

    assert order3 is not None
    assert len(order3.items()) == 0, f"Order {empty_order_id} should have no items initially"

    # Load different orders with order items, potentially affecting cache
    order1 = Order.query().with_("items").where("id = ?", (order_with_items_id,)).one()
    assert len(order1.items()) > 0, f"Order {order_with_items_id} should have items"
    assert order1.items()[0].product_name == expected_product_name

    # Query order3 again - regardless of other queries, should still have no order items
    order3_again = Order.query().with_("items").where("id = ?", (empty_order_id,)).one()

    assert order3_again is not None
    assert order3 is not order3_again, "Each query should return a new instance"
    assert len(order3_again.items()) == 0, f"Order {empty_order_id} should still have no items"

    # Add one order item to order3
    new_product_name = f"TestProduct_for_{empty_order_id}"
    new_item = OrderItem(
        order_id=empty_order_id,
        product_name=new_product_name,
        quantity=1,
        unit_price=Decimal("10.00"),
        subtotal=Decimal("10.00")
    )
    new_item.save()

    # Query again - should now have new order items
    order3_updated = Order.query().with_("items").where("id = ?", (empty_order_id,)).one()

    assert order3_updated is not None
    assert len(order3_updated.items()) == 1, f"Order {empty_order_id} should now have one item"
    assert order3_updated.items()[0].product_name == new_product_name

    # Original instance should not be affected by new queries
    assert len(order3.items()) == 0, "Original order3 instance should still show no items"
    assert len(order3_again.items()) == 0, "Second order3 instance should still show no items"


def test_cache_isolation_between_records(order_fixtures, setup_order_data):
    """Test that relation caches are properly isolated between different records."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get IDs of two orders with order items
    order_id1 = test_data.orders[0].id
    order_id2 = test_data.orders[1].id
    expected_product_name1 = test_data.items[0].product_name
    expected_product_name2 = test_data.items[1].product_name

    # Load two orders and their order items
    orders = Order.query().with_("items").where("id IN (?,?)", (order_id1, order_id2)).all()

    assert len(orders) == 2
    # Sort by ID to ensure consistent order
    orders.sort(key=lambda o: o.id)

    # Find the corresponding orders by ID
    order1 = next((o for o in orders if o.id == order_id1), None)
    order2 = next((o for o in orders if o.id == order_id2), None)

    assert order1 is not None, f"Failed to find order with id {order_id1}"
    assert order2 is not None, f"Failed to find order with id {order_id2}"

    # First order should have expected items
    assert len(order1.items()) == 1
    assert order1.items()[0].product_name == expected_product_name1

    # Second order should have expected items
    assert len(order2.items()) == 1
    assert order2.items()[
               0].product_name == expected_product_name2, f"Expected {expected_product_name2}, got {order2.items()[0].product_name}"

    # Now test separately to ensure caches don't interfere with each other
    order1 = Order.query().with_("items").where("id = ?", (order_id1,)).one()
    assert len(order1.items()) == 1
    assert order1.items()[0].product_name == expected_product_name1

    order2 = Order.query().with_("items").where("id = ?", (order_id2,)).one()
    assert len(order2.items()) == 1
    assert order2.items()[
               0].product_name == expected_product_name2, f"Expected {expected_product_name2}, got {order2.items()[0].product_name}"


def test_mixed_empty_and_populated_relations(order_fixtures, setup_order_data):
    """Test behavior when querying a mix of records with and without related data."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    order_ids = [order.id for order in test_data.orders]
    expected_product_names = [item.product_name for item in test_data.items]

    # Load all orders, including order3 without order items
    orders = Order.query().with_("items").where(f"id IN ({','.join(['?'] * len(order_ids))})", order_ids).all()

    assert len(orders) == 3, f"Expected 3 orders, got {len(orders)}"

    # Create mapping from ID to orders for consistency test
    orders_by_id = {order.id: order for order in orders}

    # Check order items for each order
    # First order has one order item
    order1 = orders_by_id[test_data.orders[0].id]
    assert len(
        order1.items()) == 1, f"Expected order {test_data.orders[0].id} to have 1 item, got {len(order1.items())}"
    assert order1.items()[0].product_name == expected_product_names[
        0], f"Expected product {expected_product_names[0]}, got {order1.items()[0].product_name}"

    # Second order has one order item
    order2 = orders_by_id[test_data.orders[1].id]
    assert len(
        order2.items()) == 1, f"Expected order {test_data.orders[1].id} to have 1 item, got {len(order2.items())}"
    assert order2.items()[0].product_name == expected_product_names[
        1], f"Expected product {expected_product_names[1]}, got {order2.items()[0].product_name}"

    # Third order has no order items
    order3 = orders_by_id[test_data.orders[2].id]
    assert len(
        order3.items()) == 0, f"Expected order {test_data.orders[2].id} to have 0 items, got {len(order3.items())}"


def test_cache_consistency_across_queries(order_fixtures, setup_order_data):
    """Test that relation cache remains consistent across multiple queries."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get empty order ID
    empty_order_id = test_data.orders[2].id

    # First query - empty order
    order = Order.query().with_("items").where("id = ?", (empty_order_id,)).one()
    assert order is not None
    assert len(order.items()) == 0, f"Expected order {empty_order_id} to have 0 items, got {len(order.items())}"

    # Add one order item to the previously empty order
    new_product_name = f"NewProduct_for_{empty_order_id}"
    new_item = OrderItem(
        order_id=empty_order_id,
        product_name=new_product_name,
        quantity=3,
        unit_price=Decimal("50.00"),
        subtotal=Decimal("150.00")
    )
    new_item.save()

    # Second query - should detect the change
    order_updated = Order.query().with_("items").where("id = ?", (empty_order_id,)).one()
    assert order_updated is not None
    assert len(
        order_updated.items()) == 1, f"Expected order {empty_order_id} to have 1 item after update, got {len(order_updated.items())}"
    assert order_updated.items()[
               0].product_name == new_product_name, f"Expected product {new_product_name}, got {order_updated.items()[0].product_name}"


def test_repeated_empty_relation_queries(order_fixtures, setup_order_data):
    """Test repeatedly querying empty relations to check for cache consistency."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get empty order ID
    empty_order_id = test_data.orders[2].id

    # Test empty relations multiple times
    for i in range(5):  # Test 5 times to increase chance of detecting issues
        order = Order.query().with_("items").where("id = ?", (empty_order_id,)).one()
        assert order is not None, f"Failed to get order {empty_order_id} on iteration {i}"
        assert len(
            order.items()) == 0, f"Expected order {empty_order_id} to have 0 items on iteration {i}, got {len(order.items())}"


def test_cache_clearing_on_update(order_fixtures, setup_order_data):
    """Test that relation cache is properly cleared when related records are updated."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get order ID with order items
    order_id = test_data.orders[0].id
    original_product_name = test_data.items[0].product_name

    # First query
    order = Order.query().with_("items").where("id = ?", (order_id,)).one()
    assert len(order.items()) == 1, f"Expected order {order_id} to have 1 item, got {len(order.items())}"
    assert order.items()[
               0].product_name == original_product_name, f"Expected product {original_product_name}, got {order.items()[0].product_name}"

    # Update order item
    item = order.items()[0]
    updated_product_name = f"{original_product_name}_Updated_{order_id}"
    item.product_name = updated_product_name
    item.save()

    # Query again - should get updated data
    order_updated = Order.query().with_("items").where("id = ?", (order_id,)).one()
    assert len(
        order_updated.items()) == 1, f"Expected order {order_id} to still have 1 item, got {len(order_updated.items())}"
    assert order_updated.items()[
               0].product_name == updated_product_name, f"Expected updated product {updated_product_name}, got {order_updated.items()[0].product_name}"


def test_relation_query_with_different_modifiers(order_fixtures, setup_order_data):
    """Test that different query modifiers don't interfere with relation caching."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get order ID and quantity info for order with items
    order_id = test_data.orders[0].id
    quantity = test_data.items[0].quantity

    # Determine high and low thresholds based on quantity
    low_threshold = max(1, quantity - 1)  # Ensure at least 1
    high_threshold = quantity + 1

    # First query - Get all order items
    order = Order.query().with_("items").where("id = ?", (order_id,)).one()
    assert len(order.items()) == 1, f"Expected order {order_id} to have 1 item, got {len(order.items())}"

    # Second query - get order items with conditions
    order_with_condition = Order.query().with_(
        ("items", lambda q: q.where("quantity > ?", (low_threshold - 1,)))  # Ensure condition is met
    ).where("id = ?", (order_id,)).one()

    assert len(
        order_with_condition.items()) == 1, f"Expected order {order_id} to have 1 item with quantity > {low_threshold - 1}, got {len(order_with_condition.items())}"

    # Third query - with different conditions
    order_with_different_condition = Order.query().with_(
        ("items", lambda q: q.where("quantity > ?", (high_threshold,)))  # Ensure condition is not met
    ).where("id = ?", (order_id,)).one()

    assert len(
        order_with_different_condition.items()) == 0, f"Expected order {order_id} to have 0 items with quantity > {high_threshold}, got {len(order_with_different_condition.items())}"


def test_relation_loading_on_empty_result_set(order_fixtures, setup_order_data):
    """Test relation loading behavior when primary query returns no results."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Query with non-existent ID
    non_existent_id = max([order.id for order in test_data.orders]) + 9999

    order = Order.query() \
        .with_("user", "items") \
        .where("id = ?", (non_existent_id,)) \
        .one()

    assert order is None, f"Expected no result for non-existent ID {non_existent_id}, but got a result"


def test_basic_relation_loading(order_fixtures, setup_order_data):
    """Test basic relation loading functionality."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Get test data
    order_id1 = test_data.orders[0].id
    order_id2 = test_data.orders[1].id
    expected_product_name1 = test_data.items[0].product_name
    expected_product_name2 = test_data.items[1].product_name

    # Test first order
    order1 = Order.query().with_("items").where("id = ?", (order_id1,)).one()
    assert len(order1.items()) == 1, f"Expected order {order_id1} to have 1 item, got {len(order1.items())}"
    assert order1.items()[0].product_name == expected_product_name1, \
        f"Expected product {expected_product_name1}, got {order1.items()[0].product_name}"

    # Test second order
    order2 = Order.query().with_("items").where("id = ?", (order_id2,)).one()
    assert len(order2.items()) == 1, f"Expected order {order_id2} to have 1 item, got {len(order2.items())}"
    assert order2.items()[0].product_name == expected_product_name2, \
        f"Expected product {expected_product_name2}, got {order2.items()[0].product_name}"

    # Test cache isolation
    order1_again = Order.query().with_("items").where("id = ?", (order_id1,)).one()
    assert len(order1_again.items()) == 1
    assert order1_again.items()[0].product_name == expected_product_name1

    order2_again = Order.query().with_("items").where("id = ?", (order_id2,)).one()
    assert len(order2_again.items()) == 1
    assert order2_again.items()[0].product_name == expected_product_name2


def test_relation_loading_with_conditions(order_fixtures, setup_order_data):
    """Test relation loading with specific conditions."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    order_id = test_data.orders[0].id
    expected_price = test_data.items[0].unit_price

    # Test loading with price condition
    order = Order.query().with_(
        ("items", lambda q: q.where("unit_price >= ?", (expected_price,)))
    ).where("id = ?", (order_id,)).one()

    assert len(order.items()) == 1
    assert order.items()[0].unit_price == expected_price


def test_relation_loading_with_ordering(order_fixtures, setup_order_data):
    """Test relation loading with specific ordering."""
    User, Order, OrderItem = order_fixtures
    test_data = setup_order_data

    # Add multiple items to first order
    order_id = test_data.orders[0].id
    new_item = OrderItem(
        order_id=order_id,
        product_name="Additional_Product",
        quantity=1,
        unit_price=Decimal("10.00"),
        subtotal=Decimal("10.00")
    )
    new_item.save()

    # Test loading with ordering
    order = Order.query().with_(
        ("items", lambda q: q.order_by("product_name ASC"))
    ).where("id = ?", (order_id,)).one()

    items = order.items()
    assert len(items) == 2
    assert items[0].product_name < items[1].product_name
