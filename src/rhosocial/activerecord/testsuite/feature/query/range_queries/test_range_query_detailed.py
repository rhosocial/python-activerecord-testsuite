# src/rhosocial/activerecord/testsuite/feature/query/range_queries/test_range_query_detailed.py
"""
Detailed RangeQueryMixin implementation tests to increase coverage of src/rhosocial/activerecord/query/range.py

This file contains specific tests for the RangeQueryMixin class,
testing their methods and functionality directly to improve code coverage.
"""

import pytest
from decimal import Decimal
from rhosocial.activerecord.query.range import RangeQueryMixin
from rhosocial.activerecord.backend.dialect.protocols import ILIKESupport


def test_get_col_expr_with_string_column(order_fixtures):
    """Test _get_col_expr method with string column."""
    User, Order, OrderItem = order_fixtures

    # Since RangeQueryMixin is a mixin, we test it through a concrete class that inherits from it
    # We'll use the query method of a model which should have RangeQueryMixin functionality
    query = Order.query()

    # Test with string column
    col_expr = query._get_col_expr('status')
    assert col_expr is not None
    assert hasattr(col_expr, 'to_sql')  # Should be a Column expression


def test_get_col_expr_with_base_expression(order_fixtures):
    """Test _get_col_expr method with BaseExpression."""
    User, Order, OrderItem = order_fixtures

    query = Order.query()

    # Test with BaseExpression (using field proxy)
    base_expr = Order.c.status
    col_expr = query._get_col_expr(base_expr)

    assert col_expr is base_expr  # Should return the same object


def test_get_col_expr_with_invalid_type(order_fixtures):
    """Test _get_col_expr method with invalid type raises TypeError."""
    User, Order, OrderItem = order_fixtures

    query = Order.query()

    # Test with invalid type
    with pytest.raises(TypeError, match="column must be a string or a BaseExpression"):
        query._get_col_expr(123)  # Integer is not valid


def test_in_list_with_values(order_fixtures):
    """Test in_list method with values."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=35)
    user3.save()

    # Test in_list with values
    results = User.query().in_list(User.c.username, ['user1', 'user2']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' not in usernames


def test_in_list_with_empty_list_default_behavior(order_fixtures):
    """Test in_list method with empty list (default behavior)."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    # Test in_list with empty list (default: empty_result=True, so should return no results)
    results = User.query().in_list(User.c.username, []).all()

    assert len(results) == 0


def test_in_list_with_empty_list_no_result_false(order_fixtures):
    """Test in_list method with empty list and empty_result=False."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    # Test in_list with empty list and empty_result=False (should return all results)
    all_users = User.query().all()
    results = User.query().in_list(User.c.username, [], empty_result=False).all()

    assert len(results) == len(all_users)


def test_in_list_with_string_column_name(order_fixtures):
    """Test in_list method with string column name."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    # Test in_list with string column name
    results = User.query().in_list('username', ['user1', 'user2']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames


def test_not_in_with_values(order_fixtures):
    """Test not_in method with values."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=35)
    user3.save()

    # Test not_in with values
    results = User.query().not_in(User.c.username, ['user3']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' not in usernames


def test_not_in_with_empty_list_default_behavior(order_fixtures):
    """Test not_in method with empty list (default behavior)."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    # Test not_in with empty list (default: empty_result=False, so should return all results)
    all_users = User.query().all()
    results = User.query().not_in(User.c.username, []).all()

    assert len(results) == len(all_users)


def test_not_in_with_empty_list_empty_result_true(order_fixtures):
    """Test not_in method with empty list and empty_result=True."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    # Test not_in with empty list and empty_result=True (should return no results)
    results = User.query().not_in(User.c.username, [], empty_result=True).all()

    assert len(results) == 0


def test_not_in_with_string_column_name(order_fixtures):
    """Test not_in method with string column name."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=35)
    user3.save()

    # Test not_in with string column name
    results = User.query().not_in('username', ['user3']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' not in usernames


def test_between_method(order_fixtures):
    """Test between method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30)
    user3.save()

    user4 = User(username='user4', email='user4@example.com', age=35)
    user4.save()

    # Test between method
    results = User.query().between(User.c.age, 22, 32).all()

    # Should return user2 (25) and user3 (30) - 2 results
    assert len(results) == 2
    ages = [u.age for u in results]
    assert 25 in ages  # user2
    assert 30 in ages  # user3
    assert 20 not in ages  # user1 is too young
    assert 35 not in ages  # user4 is too old


def test_between_with_string_column_name(order_fixtures):
    """Test between method with string column name."""
    User, Order, OrderItem = order_fixtures

    # Create test data with balances
    user1 = User(username='user1', email='user1@example.com', age=25, balance=100.0)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30, balance=200.0)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=35, balance=300.0)
    user3.save()

    # Test between with string column name
    results = User.query().between('balance', 150.0, 250.0).all()

    assert len(results) == 1  # user2 (200.0) should match
    balances = [u.balance for u in results]
    assert 200.0 in balances  # user2
    assert 100.0 not in balances  # user1 is too low
    assert 300.0 not in balances  # user3 is too high


def test_not_between_method(order_fixtures):
    """Test not_between method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30)
    user3.save()

    user4 = User(username='user4', email='user4@example.com', age=35)
    user4.save()

    # Test not_between method
    results = User.query().not_between(User.c.age, 22, 32).all()

    assert len(results) == 2  # user1 (20) and user4 (35) should be outside the range
    ages = [u.age for u in results]
    assert 20 in ages  # user1
    assert 35 in ages  # user4
    assert 25 not in ages  # user2 is in range
    assert 30 not in ages  # user3 is in range


def test_not_between_with_string_column_name(order_fixtures):
    """Test not_between method with string column name."""
    User, Order, OrderItem = order_fixtures

    # Create test data with balances
    user1 = User(username='user1', email='user1@example.com', age=25, balance=100.0)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30, balance=200.0)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=35, balance=300.0)
    user3.save()

    # Test not_between with string column name
    results = User.query().not_between('balance', 150.0, 250.0).all()

    assert len(results) == 2  # user1 (100.0) and user3 (300.0) should be outside range
    balances = [u.balance for u in results]
    assert 100.0 in balances  # user1
    assert 300.0 in balances  # user3
    assert 200.0 not in balances  # user2 is in range


def test_like_method(order_fixtures):
    """Test like method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='alice_smith', email='alice@example.com', age=25)
    user1.save()

    user2 = User(username='bob_jones', email='bob@example.com', age=30)
    user2.save()

    user3 = User(username='charlie_brown', email='charlie@example.com', age=35)
    user3.save()

    # Test like method with pattern
    results = User.query().like(User.c.username, '%smith%').all()

    assert len(results) == 1
    assert results[0].username == 'alice_smith'


def test_like_with_string_column_name(order_fixtures):
    """Test like method with string column name."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='alice_smith', email='alice@example.com', age=25)
    user1.save()

    user2 = User(username='bob_jones', email='bob@example.com', age=30)
    user2.save()

    # Test like with string column name
    results = User.query().like('username', '%jones%').all()

    assert len(results) == 1
    assert results[0].username == 'bob_jones'


def test_not_like_method(order_fixtures):
    """Test not_like method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='alice_smith', email='alice@example.com', age=25)
    user1.save()

    user2 = User(username='bob_jones', email='bob@example.com', age=30)
    user2.save()

    user3 = User(username='charlie_smith', email='charlie@example.com', age=35)
    user3.save()

    # Test not_like method
    results = User.query().not_like(User.c.username, '%smith%').all()

    assert len(results) == 1
    assert results[0].username == 'bob_jones'


def test_like_with_string_column_name(order_fixtures):
    """Additional test for like method with string column name."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='john_doe', email='john@example.com', age=25)
    user1.save()

    user2 = User(username='jane_doe', email='jane@example.com', age=30)
    user2.save()

    user3 = User(username='bob_smith', email='bob@example.com', age=35)
    user3.save()

    # Test like with string column name for different patterns
    # Test pattern at beginning
    results_start = User.query().like('username', 'john%').all()
    assert len(results_start) == 1
    assert results_start[0].username == 'john_doe'

    # Test pattern at end
    results_end = User.query().like('username', '%_doe').all()
    assert len(results_end) == 2  # john_doe and jane_doe
    usernames = {u.username for u in results_end}
    assert usernames == {'john_doe', 'jane_doe'}

    # Test pattern in middle
    results_middle = User.query().like('username', '%_%').all()  # Contains underscore
    assert len(results_middle) == 3  # All users have underscores


def test_like_with_wildcards(order_fixtures):
    """Test like method with various wildcard patterns."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='a_test_user', email='a@example.com', age=25)
    user1.save()

    user2 = User(username='b_another_user', email='b@example.com', age=30)
    user2.save()

    user3 = User(username='c_tester_user', email='c@example.com', age=35)
    user3.save()

    # Test various wildcard patterns
    # Single character wildcard (_)
    results_single = User.query().like(User.c.username, 'a_test_user').all()  # Exact match
    assert len(results_single) == 1
    assert results_single[0].username == 'a_test_user'

    # Multiple character wildcard (%)
    results_multi = User.query().like(User.c.username, '%test%').all()  # Contains 'test'
    assert len(results_multi) == 2  # a_test_user and c_tester_user
    usernames = {u.username for u in results_multi}
    assert 'a_test_user' in usernames
    assert 'c_tester_user' in usernames
    assert 'b_another_user' not in usernames


@pytest.mark.requires_protocol((ILIKESupport, "supports_ilike"))
def test_ilike_method(order_fixtures):
    """Test ilike method (case-insensitive like)."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='Alice_Smith', email='alice@example.com', age=25)
    user1.save()

    user2 = User(username='BOB_JONES', email='bob@example.com', age=30)
    user2.save()

    user3 = User(username='charlie_BROWN', email='charlie@example.com', age=35)
    user3.save()

    # Test ilike method with case-insensitive pattern
    results = User.query().ilike(User.c.username, '%smith%').all()

    # Should match Alice_Smith despite case difference
    assert len(results) == 1
    assert results[0].username.lower().find('smith') != -1


@pytest.mark.requires_protocol((ILIKESupport, "supports_ilike"))
def test_not_ilike_method(order_fixtures):
    """Test not_ilike method (case-insensitive not like)."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='Alice_Smith', email='alice@example.com', age=25)
    user1.save()

    user2 = User(username='BOB_JONES', email='bob@example.com', age=30)
    user2.save()

    user3 = User(username='charlie_smith', email='charlie@example.com', age=35)
    user3.save()

    # Test not_ilike method
    results = User.query().not_ilike(User.c.username, '%smith%').all()

    # Should return bob_jones who doesn't contain smith (case insensitive)
    assert len(results) == 1
    assert results[0].username == 'BOB_JONES'


def test_is_null_method(order_fixtures):
    """Test is_null method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    # Create a user with a specific field that could be null
    # For this test, we'll use a field that might be null in some records
    user2 = User(username='user2', email='user2@example.com', age=None)  # age is optional
    user2.save()

    # Test is_null method
    results = User.query().is_null(User.c.age).all()

    # Find how many users have null age
    null_age_count = sum(1 for u in User.query().all() if u.age is None)
    assert len(results) == null_age_count


def test_is_not_null_method(order_fixtures):
    """Test is_not_null method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=25)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=30)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=None)  # age is null
    user3.save()

    # Test is_not_null method
    results = User.query().is_not_null(User.c.age).all()

    # Should return users with non-null age
    assert len(results) >= 2  # At least user1 and user2
    for user in results:
        assert user.age is not None


def test_greater_than_method(order_fixtures):
    """Test greater_than method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30)
    user3.save()

    # Test greater_than method
    results = User.query().greater_than(User.c.age, 22).all()

    assert len(results) == 2  # user2 (25) and user3 (30)
    ages = [u.age for u in results]
    assert 25 in ages
    assert 30 in ages
    assert 20 not in ages


def test_greater_than_or_equal_method(order_fixtures):
    """Test greater_than_or_equal method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30)
    user3.save()

    # Test greater_than_or_equal method
    results = User.query().greater_than_or_equal(User.c.age, 25).all()

    assert len(results) == 2  # user2 (25) and user3 (30)
    ages = [u.age for u in results]
    assert 25 in ages
    assert 30 in ages
    assert 20 not in ages


def test_less_than_method(order_fixtures):
    """Test less_than method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30)
    user3.save()

    # Test less_than method
    results = User.query().less_than(User.c.age, 28).all()

    assert len(results) == 2  # user1 (20) and user2 (25)
    ages = [u.age for u in results]
    assert 20 in ages
    assert 25 in ages
    assert 30 not in ages


def test_less_than_or_equal_method(order_fixtures):
    """Test less_than_or_equal method."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30)
    user3.save()

    # Test less_than_or_equal method
    results = User.query().less_than_or_equal(User.c.age, 25).all()

    assert len(results) == 2  # user1 (20) and user2 (25)
    ages = [u.age for u in results]
    assert 20 in ages
    assert 25 in ages
    assert 30 not in ages


def test_chaining_range_methods(order_fixtures):
    """Test chaining multiple range methods."""
    User, Order, OrderItem = order_fixtures

    # Create test data
    user1 = User(username='user1', email='user1@example.com', age=20, balance=100.0)
    user1.save()

    user2 = User(username='user2', email='user2@example.com', age=25, balance=200.0)
    user2.save()

    user3 = User(username='user3', email='user3@example.com', age=30, balance=300.0)
    user3.save()

    user4 = User(username='user4', email='user4@example.com', age=35, balance=400.0)
    user4.save()

    # Test chaining multiple range methods
    results = (User.query()
               .greater_than(User.c.age, 22)
               .less_than(User.c.age, 33)
               .greater_than_or_equal(User.c.balance, 200.0)
               .all())

    # Should match user2 (age=25, balance=200.0) and user3 (age=30, balance=300.0)
    assert len(results) == 2
    usernames = {u.username for u in results}
    assert 'user2' in usernames
    assert 'user3' in usernames
    assert 'user1' not in usernames  # Too young
    assert 'user4' not in usernames  # Too old