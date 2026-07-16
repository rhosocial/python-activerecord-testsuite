# src/rhosocial/activerecord/testsuite/feature/query/range_queries/test_range_query_detailed_async.py
"""
Detailed RangeQueryMixin implementation tests to increase coverage of src/rhosocial/activerecord/query/range.py

This file contains specific tests for the RangeQueryMixin class,
testing their methods and functionality directly to improve code coverage.
"""

import pytest
from decimal import Decimal
from rhosocial.activerecord.query.range import RangeQueryMixin
from rhosocial.activerecord.backend.dialect.protocols import ILIKESupport


async def test_get_col_expr_with_string_column(async_order_fixtures):
    """Test _get_col_expr method with string column."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Since RangeQueryMixin is a mixin, we test it through a concrete class that inherits from it
    # We'll use the query method of a model which should have RangeQueryMixin functionality
    query = AsyncOrder.query()

    # Test with string column
    col_expr = query._get_col_expr('status')
    assert col_expr is not None
    assert hasattr(col_expr, 'to_sql')  # Should be a Column expression


async def test_get_col_expr_with_base_expression(async_order_fixtures):
    """Test _get_col_expr method with BaseExpression."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    query = AsyncOrder.query()

    # Test with BaseExpression (using field proxy)
    base_expr = AsyncOrder.c.status
    col_expr = query._get_col_expr(base_expr)

    assert col_expr is base_expr  # Should return the same object


async def test_get_col_expr_with_invalid_type(async_order_fixtures):
    """Test _get_col_expr method with invalid type raises TypeError."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    query = AsyncOrder.query()

    # Test with invalid type
    with pytest.raises(TypeError, match="column must be a string or a BaseExpression"):
        query._get_col_expr(123)  # Integer is not valid


async def test_in_list_with_values(async_order_fixtures):
    """Test in_list method with values."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=35)
    await user3.save()

    # Test in_list with values
    results = await AsyncUser.query().in_list(AsyncUser.c.username, ['user1', 'user2']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' not in usernames


async def test_in_list_with_empty_list_default_behavior(async_order_fixtures):
    """Test in_list method with empty list (default behavior)."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    # Test in_list with empty list (default: empty_result=True, so should return no results)
    results = await AsyncUser.query().in_list(AsyncUser.c.username, []).all()

    assert len(results) == 0


async def test_in_list_with_empty_list_no_result_false(async_order_fixtures):
    """Test in_list method with empty list and empty_result=False."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    # Test in_list with empty list and empty_result=False (should return all results)
    all_users = await AsyncUser.query().all()
    results = await AsyncUser.query().in_list(AsyncUser.c.username, [], empty_result=False).all()

    assert len(results) == len(all_users)


async def test_in_list_with_string_column_name(async_order_fixtures):
    """Test in_list method with string column name."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    # Test in_list with string column name
    results = await AsyncUser.query().in_list('username', ['user1', 'user2']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames


async def test_not_in_with_values(async_order_fixtures):
    """Test not_in method with values."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=35)
    await user3.save()

    # Test not_in with values
    results = await AsyncUser.query().not_in(AsyncUser.c.username, ['user3']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' not in usernames


async def test_not_in_with_empty_list_default_behavior(async_order_fixtures):
    """Test not_in method with empty list (default behavior)."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    # Test not_in with empty list (default: empty_result=False, so should return all results)
    all_users = await AsyncUser.query().all()
    results = await AsyncUser.query().not_in(AsyncUser.c.username, []).all()

    assert len(results) == len(all_users)


async def test_not_in_with_empty_list_empty_result_true(async_order_fixtures):
    """Test not_in method with empty list and empty_result=True."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    # Test not_in with empty list and empty_result=True (should return no results)
    results = await AsyncUser.query().not_in(AsyncUser.c.username, [], empty_result=True).all()

    assert len(results) == 0


async def test_not_in_with_string_column_name(async_order_fixtures):
    """Test not_in method with string column name."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=35)
    await user3.save()

    # Test not_in with string column name
    results = await AsyncUser.query().not_in('username', ['user3']).all()

    assert len(results) == 2
    usernames = [u.username for u in results]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' not in usernames


async def test_between_method(async_order_fixtures):
    """Test between method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30)
    await user3.save()

    user4 = AsyncUser(username='user4', email='user4@example.com', age=35)
    await user4.save()

    # Test between method
    results = await AsyncUser.query().between(AsyncUser.c.age, 22, 32).all()

    # Should return user2 (25) and user3 (30) - 2 results
    assert len(results) == 2
    ages = [u.age for u in results]
    assert 25 in ages  # user2
    assert 30 in ages  # user3
    assert 20 not in ages  # user1 is too young
    assert 35 not in ages  # user4 is too old


async def test_between_with_string_column_name(async_order_fixtures):
    """Test between method with string column name."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data with balances
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25, balance=100.0)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30, balance=200.0)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=35, balance=300.0)
    await user3.save()

    # Test between with string column name
    results = await AsyncUser.query().between('balance', 150.0, 250.0).all()

    assert len(results) == 1  # user2 (200.0) should match
    balances = [u.balance for u in results]
    assert 200.0 in balances  # user2
    assert 100.0 not in balances  # user1 is too low
    assert 300.0 not in balances  # user3 is too high


async def test_not_between_method(async_order_fixtures):
    """Test not_between method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30)
    await user3.save()

    user4 = AsyncUser(username='user4', email='user4@example.com', age=35)
    await user4.save()

    # Test not_between method
    results = await AsyncUser.query().not_between(AsyncUser.c.age, 22, 32).all()

    assert len(results) == 2  # user1 (20) and user4 (35) should be outside the range
    ages = [u.age for u in results]
    assert 20 in ages  # user1
    assert 35 in ages  # user4
    assert 25 not in ages  # user2 is in range
    assert 30 not in ages  # user3 is in range


async def test_not_between_with_string_column_name(async_order_fixtures):
    """Test not_between method with string column name."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data with balances
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25, balance=100.0)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30, balance=200.0)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=35, balance=300.0)
    await user3.save()

    # Test not_between with string column name
    results = await AsyncUser.query().not_between('balance', 150.0, 250.0).all()

    assert len(results) == 2  # user1 (100.0) and user3 (300.0) should be outside range
    balances = [u.balance for u in results]
    assert 100.0 in balances  # user1
    assert 300.0 in balances  # user3
    assert 200.0 not in balances  # user2 is in range


async def test_like_method(async_order_fixtures):
    """Test like method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='alice_smith', email='alice@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='bob_jones', email='bob@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='charlie_brown', email='charlie@example.com', age=35)
    await user3.save()

    # Test like method with pattern
    results = await AsyncUser.query().like(AsyncUser.c.username, '%smith%').all()

    assert len(results) == 1
    assert results[0].username == 'alice_smith'


async def test_like_with_string_column_name(async_order_fixtures):
    """Test like method with string column name."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='alice_smith', email='alice@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='bob_jones', email='bob@example.com', age=30)
    await user2.save()

    # Test like with string column name
    results = await AsyncUser.query().like('username', '%jones%').all()

    assert len(results) == 1
    assert results[0].username == 'bob_jones'


async def test_not_like_method(async_order_fixtures):
    """Test not_like method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='alice_smith', email='alice@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='bob_jones', email='bob@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='charlie_smith', email='charlie@example.com', age=35)
    await user3.save()

    # Test not_like method
    results = await AsyncUser.query().not_like(AsyncUser.c.username, '%smith%').all()

    assert len(results) == 1
    assert results[0].username == 'bob_jones'


async def test_like_with_string_column_name(async_order_fixtures):
    """Additional test for like method with string column name."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='john_doe', email='john@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='jane_doe', email='jane@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='bob_smith', email='bob@example.com', age=35)
    await user3.save()

    # Test like with string column name for different patterns
    # Test pattern at beginning
    results_start = await AsyncUser.query().like('username', 'john%').all()
    assert len(results_start) == 1
    assert results_start[0].username == 'john_doe'

    # Test pattern at end
    results_end = await AsyncUser.query().like('username', '%_doe').all()
    assert len(results_end) == 2  # john_doe and jane_doe
    usernames = {u.username for u in results_end}
    assert usernames == {'john_doe', 'jane_doe'}

    # Test pattern in middle
    results_middle = await AsyncUser.query().like('username', '%_%').all()  # Contains underscore
    assert len(results_middle) == 3  # All users have underscores


async def test_like_with_wildcards(async_order_fixtures):
    """Test like method with various wildcard patterns."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='a_test_user', email='a@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='b_another_user', email='b@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='c_tester_user', email='c@example.com', age=35)
    await user3.save()

    # Test various wildcard patterns
    # Single character wildcard (_)
    results_single = await AsyncUser.query().like(AsyncUser.c.username, 'a_test_user').all()  # Exact match
    assert len(results_single) == 1
    assert results_single[0].username == 'a_test_user'

    # Multiple character wildcard (%)
    results_multi = await AsyncUser.query().like(AsyncUser.c.username, '%test%').all()  # Contains 'test'
    assert len(results_multi) == 2  # a_test_user and c_tester_user
    usernames = {u.username for u in results_multi}
    assert 'a_test_user' in usernames
    assert 'c_tester_user' in usernames
    assert 'b_another_user' not in usernames


@pytest.mark.requires_protocol((ILIKESupport, "supports_ilike"))
async def test_ilike_method(async_order_fixtures):
    """Test ilike method (case-insensitive like)."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='Alice_Smith', email='alice@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='BOB_JONES', email='bob@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='charlie_BROWN', email='charlie@example.com', age=35)
    await user3.save()

    # Test ilike method with case-insensitive pattern
    results = await AsyncUser.query().ilike(AsyncUser.c.username, '%smith%').all()

    # Should match Alice_Smith despite case difference
    assert len(results) == 1
    assert results[0].username.lower().find('smith') != -1


@pytest.mark.requires_protocol((ILIKESupport, "supports_ilike"))
async def test_not_ilike_method(async_order_fixtures):
    """Test not_ilike method (case-insensitive not like)."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='Alice_Smith', email='alice@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='BOB_JONES', email='bob@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='charlie_smith', email='charlie@example.com', age=35)
    await user3.save()

    # Test not_ilike method
    results = await AsyncUser.query().not_ilike(AsyncUser.c.username, '%smith%').all()

    # Should return bob_jones who doesn't contain smith (case insensitive)
    assert len(results) == 1
    assert results[0].username == 'BOB_JONES'


async def test_is_null_method(async_order_fixtures):
    """Test is_null method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    # Create a user with a specific field that could be null
    # For this test, we'll use a field that might be null in some records
    user2 = AsyncUser(username='user2', email='user2@example.com', age=None)  # age is optional
    await user2.save()

    # Test is_null method
    results = await AsyncUser.query().is_null(AsyncUser.c.age).all()

    # Find how many users have null age
    null_age_count = sum(1 for u in await AsyncUser.query().all() if u.age is None)
    assert len(results) == null_age_count


async def test_is_not_null_method(async_order_fixtures):
    """Test is_not_null method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=None)  # age is null
    await user3.save()

    # Test is_not_null method
    results = await AsyncUser.query().is_not_null(AsyncUser.c.age).all()

    # Should return users with non-null age
    assert len(results) >= 2  # At least user1 and user2
    for user in results:
        assert user.age is not None


async def test_greater_than_method(async_order_fixtures):
    """Test greater_than method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30)
    await user3.save()

    # Test greater_than method
    results = await AsyncUser.query().greater_than(AsyncUser.c.age, 22).all()

    assert len(results) == 2  # user2 (25) and user3 (30)
    ages = [u.age for u in results]
    assert 25 in ages
    assert 30 in ages
    assert 20 not in ages


async def test_greater_than_or_equal_method(async_order_fixtures):
    """Test greater_than_or_equal method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30)
    await user3.save()

    # Test greater_than_or_equal method
    results = await AsyncUser.query().greater_than_or_equal(AsyncUser.c.age, 25).all()

    assert len(results) == 2  # user2 (25) and user3 (30)
    ages = [u.age for u in results]
    assert 25 in ages
    assert 30 in ages
    assert 20 not in ages


async def test_less_than_method(async_order_fixtures):
    """Test less_than method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30)
    await user3.save()

    # Test less_than method
    results = await AsyncUser.query().less_than(AsyncUser.c.age, 28).all()

    assert len(results) == 2  # user1 (20) and user2 (25)
    ages = [u.age for u in results]
    assert 20 in ages
    assert 25 in ages
    assert 30 not in ages


async def test_less_than_or_equal_method(async_order_fixtures):
    """Test less_than_or_equal method."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30)
    await user3.save()

    # Test less_than_or_equal method
    results = await AsyncUser.query().less_than_or_equal(AsyncUser.c.age, 25).all()

    assert len(results) == 2  # user1 (20) and user2 (25)
    ages = [u.age for u in results]
    assert 20 in ages
    assert 25 in ages
    assert 30 not in ages


async def test_chaining_range_methods(async_order_fixtures):
    """Test chaining multiple range methods."""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data
    user1 = AsyncUser(username='user1', email='user1@example.com', age=20, balance=100.0)
    await user1.save()

    user2 = AsyncUser(username='user2', email='user2@example.com', age=25, balance=200.0)
    await user2.save()

    user3 = AsyncUser(username='user3', email='user3@example.com', age=30, balance=300.0)
    await user3.save()

    user4 = AsyncUser(username='user4', email='user4@example.com', age=35, balance=400.0)
    await user4.save()

    # Test chaining multiple range methods
    results = (await AsyncUser.query()
               .greater_than(AsyncUser.c.age, 22)
               .less_than(AsyncUser.c.age, 33)
               .greater_than_or_equal(AsyncUser.c.balance, 200.0)
               .all())

    # Should match user2 (age=25, balance=200.0) and user3 (age=30, balance=300.0)
    assert len(results) == 2
    usernames = {u.username for u in results}
    assert 'user2' in usernames
    assert 'user3' in usernames
    assert 'user1' not in usernames  # Too young
    assert 'user4' not in usernames  # Too old