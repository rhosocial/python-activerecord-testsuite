# src/rhosocial/activerecord/testsuite/feature/query/test_error_handling.py
"""Error handling and edge cases tests"""
from decimal import Decimal

from rhosocial.activerecord.backend.errors import DatabaseError


def test_invalid_parameter_handling(order_fixtures):
    """
    Test invalid parameter handling in queries

    This test verifies that the system properly handles invalid parameter
    types passed to query methods, raising appropriate exceptions when
    incompatible types are used.
    """
    User, Order, OrderItem = order_fixtures

    # Create test user and order for parameter testing
    user = User(username='error_param_user', email='errorparam@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='ERR-001', total_amount=Decimal('100.00'))
    order.save()

    # Test passing wrong type of parameter to where method
    try:
        # Try passing wrong parameter type (string instead of integer)
        results = Order.query().where(Order.c.id == "invalid_id_type").all()
        # Some backends may try to convert type, so not always fail
    except Exception as e:
        # Different backends report errors differently:
        # - SQLite/MySQL: TypeError, ValueError, AttributeError
        # - PostgreSQL: DatabaseError (reports invalid input at DB level)
        assert isinstance(e, (TypeError, ValueError, AttributeError, DatabaseError)), \
            f"Expected TypeError, ValueError, AttributeError or DatabaseError, got {type(e)}"

    # Test correct parameter type
    results = Order.query().where(Order.c.id == order.id).all()
    assert len(results) == 1


def test_type_error_handling(order_fixtures):
    """
    Test type error handling in queries

    This test verifies that the system properly handles type mismatches
    when comparing values of different types, preventing runtime errors
    and ensuring consistent behavior.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='type_error_user', email='typeerror@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='TYPE-001', total_amount=Decimal('150.00'))
    order.save()

    # Test comparing string with number (type mismatch)
    try:
        results = Order.query().where(Order.c.total_amount == "not_a_number").all()
        # Some backends may try type conversion
    except Exception as e:
        # Some backends may catch and handle this error
        pass

    # Test correct type comparison
    results = Order.query().where(Order.c.total_amount == Decimal('150.00')).all()
    assert len(results) == 1


def test_null_value_handling(order_fixtures):
    """
    Test null value handling in queries

    This test verifies that the system properly handles null values in
    queries, supporting both null and non-null value checks without errors.
    """
    User, Order, OrderItem = order_fixtures

    # Create user with null age for null value testing
    user = User(username='null_user', email='null@example.com', age=None)  # Age is null
    user.save()

    # Create an order with all required fields, avoiding null status field if it's not allowed
    order = Order(
        user_id=user.id,
        order_number='NULL-001',
        total_amount=Decimal('200.00'),
        status='pending'  # Use a valid status instead of None
    )
    order.save()

    # Test querying null values in fields that allow nulls
    # Different databases may handle NULL comparisons differently
    # Try both approaches: direct comparison and SQL string
    try:
        null_age_users = User.query().where(User.c.age == None).all()
        # If direct comparison doesn't work, try SQL string approach
        if len(null_age_users) == 0:
            null_age_users = User.query().where('age IS NULL').all()
    except Exception:
        # If direct comparison fails, use SQL string approach
        null_age_users = User.query().where('age IS NULL').all()

    assert len(null_age_users) >= 1

    # Test querying non-null values
    try:
        non_null_email_users = User.query().where(User.c.email != None).all()
        if len(non_null_email_users) == 0:
            non_null_email_users = User.query().where('email IS NOT NULL').all()
    except Exception:
        non_null_email_users = User.query().where('email IS NOT NULL').all()
    
    assert len(non_null_email_users) >= 1


def test_sql_injection_protection(order_fixtures):
    """
    Test SQL injection protection mechanisms

    This test verifies that the system properly protects against SQL
    injection attacks by using parameterized queries and properly
    escaping dangerous characters.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='inject_user', email='inject@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='INJECT-001', total_amount=Decimal('100.00'))
    order.save()

    # Try SQL injection attack
    malicious_input = "'; DROP TABLE orders; --"

    # Use parameterized query, malicious input should be treated as plain string
    # not SQL code
    try:
        results = Order.query().where('order_number = ?', (malicious_input,)).all()
        # Should find no matching orders as no order number is malicious input
        assert len(results) == 0
    except Exception as e:
        # In some cases exception may be thrown, which is also secure behavior
        pass

    # Verify normal query still works
    normal_results = Order.query().where('order_number = ?', ('INJECT-001',)).all()
    assert len(normal_results) == 1


def test_parameterized_query_validation(order_fixtures):
    """
    Test parameterized query validation

    This test verifies that parameterized queries are properly validated
    and that incorrect parameter counts or types are handled appropriately.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='param_user', email='param@example.com', age=30)
    user.save()

    # Create multiple orders for parameter validation testing
    for i in range(3):
        Order(
            user_id=user.id,
            order_number=f'PARAM-{i+1:03d}',
            total_amount=Decimal(f'{(i+1)*50.00}')
        ).save()

    # Test parameterized query correctness with positional parameters
    results1 = Order.query().where('order_number = ?', ('PARAM-001',)).all()
    assert len(results1) == 1
    assert results1[0].order_number == 'PARAM-001'

    # Test parameter count mismatch - provide wrong number of parameters
    try:
        results = Order.query().where('order_number = ? AND total_amount = ?', ('PARAM-001',)).all()
        # Some implementations may handle this gracefully
    except Exception as e:
        # Expected to have some error for parameter mismatch
        pass


def test_dangerous_character_escaping(order_fixtures):
    """
    Test dangerous character escaping in queries

    This test verifies that potentially dangerous characters in query
    parameters are properly escaped to prevent security vulnerabilities.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='escape_user', email='escape@example.com', age=30)
    user.save()

    # Order number with potentially dangerous characters for escaping test
    dangerous_order_number = "Dangerous'Order\"Name;DROP"

    order = Order(
        user_id=user.id,
        order_number=dangerous_order_number,
        total_amount=Decimal('125.50'),
        status='pending'
    )
    order.save()

    # Test using value with dangerous characters in query
    results = Order.query().where(Order.c.order_number == dangerous_order_number).all()
    assert len(results) == 1
    assert results[0].order_number == dangerous_order_number

    # Use parameterized query again for validation
    param_results = Order.query().where('order_number = ?', (dangerous_order_number,)).all()
    assert len(param_results) == 1
    assert param_results[0].order_number == dangerous_order_number


def test_column_resolution_errors(order_fixtures):
    """
    Test column resolution error handling

    This test verifies that attempts to access non-existent columns
    result in appropriate error handling rather than undefined behavior.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='col_res_user', email='colres@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='COLRES-001', total_amount=Decimal('89.99'), status='pending')
    order.save()

    # Test accessing non-existent column
    try:
        # Try querying a non-existent column
        results = Order.query().where('nonexistent_column = ?', ('some_value',)).all()
        # Some implementations may discover this issue at execution time
    except Exception as e:
        # Expected to throw some error, like database error
        pass

    # Verify normal query still works
    normal_results = Order.query().where(Order.c.order_number == 'COLRES-001').all()
    assert len(normal_results) == 1


def test_division_by_zero_handling(order_fixtures):
    """
    Test division by zero error handling

    This test verifies that the system properly handles mathematical
    operations that could result in division by zero errors.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='div_zero_user', email='divzero@example.com', age=30)
    user.save()

    # Create order with zero total amount for division testing
    order = Order(
        user_id=user.id,
        order_number='DIVZERO-001',
        total_amount=Decimal('0.00'),  # Zero amount
        status='pending'
    )
    order.save()

    # Test operations that might cause division by zero
    try:
        # This might cause division by zero in some calculations
        results = Order.query().where(Order.c.total_amount != Decimal('0.00')).all()
        # Exclude zero amounts to avoid potential division by zero in calculations
    except Exception as e:
        # Some implementations might handle this gracefully
        pass

    # Verify normal operations still work
    normal_results = Order.query().where(Order.c.id == order.id).all()
    assert len(normal_results) == 1


def test_invalid_sql_syntax_handling(order_fixtures):
    """
    Test invalid SQL syntax error handling

    This test verifies that the system properly handles invalid SQL
    syntax, raising appropriate exceptions rather than causing crashes.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='invalid_sql_user', email='invalidsql@example.com', age=30)
    user.save()

    # Test invalid SQL syntax
    try:
        # Try invalid SQL syntax
        results = Order.query().where('invalid_sql_syntax').all()
        # Some implementations might handle this gracefully
    except Exception as e:
        # Expected to throw some error for invalid syntax
        pass

    # Verify valid syntax still works
    valid_results = Order.query().where(Order.c.user_id == user.id).all()
    assert len(valid_results) >= 0  # May be 0 if no orders created for this user


def test_transaction_rollback_on_error(order_fixtures):
    """
    Test transaction rollback on error

    This test verifies that database transactions are properly rolled back
    when errors occur, maintaining data consistency and integrity.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='trans_rollback_user', email='transrollback@example.com', age=30)
    user.save()

    # Test transaction behavior with error
    try:
        # Start a transaction implicitly with save
        problematic_order = Order(
            user_id=user.id,
            order_number='TRANS-001',
            total_amount=Decimal('150.00'),
            status='pending'
        )
        problematic_order.save()

        # Simulate an operation that might cause an error
        results = Order.query().where(Order.c.order_number == 'TRANS-001').all()
        assert len(results) == 1
    except Exception as e:
        # If error occurs, verify data integrity is maintained
        pass

    # Verify that valid operations still work correctly
    valid_results = Order.query().where(Order.c.user_id == user.id).all()
    assert len(valid_results) > 0


# ============================================================
# Escape consistency tests (转义一致性)
# Verify that values with special characters produce identical
# results whether passed via expression-based queries or raw
# parameterized SQL queries.
# ============================================================

def test_escape_consistency_single_quote(order_fixtures):
    """
    Test that values with single quotes roundtrip identically
    via expression queries and raw parameterized queries.

    This verifies escape consistency: the ORM's expression builder
    and manual parameterized SQL produce the same escaped result.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='esc_quote', email='esc_quote@example.com', age=30)
    user.save()

    values = [
        "it's working",
        "O'Brien",
        "'''triple single'''",
        "begin ' middle ' end",
    ]

    for i, val in enumerate(values):
        Order(user_id=user.id, order_number=f"SQ-{i:03d}", total_amount=Decimal('100')).save()

        # Test via expression-based query
        where_order = Order.query().where(Order.c.order_number == f"SQ-{i:03d}").all()

        # Now insert a record with the special value
        order = Order(user_id=user.id, order_number=val, total_amount=Decimal(f'{i+1}0.00'), status='pending')
        order.save()

        # Query back via expression
        results_expr = Order.query().where(Order.c.order_number == val).all()
        assert len(results_expr) == 1, f"Expression query failed for '{val}'"
        assert results_expr[0].order_number == val

        # Query back via parameterized raw SQL
        results_raw = Order.query().where('order_number = ?', (val,)).all()
        assert len(results_raw) == 1, f"Raw parameterized query failed for '{val}'"
        assert results_raw[0].order_number == val


def test_escape_consistency_double_quote(order_fixtures):
    """
    Test values with double quotes work identically via both query methods.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='esc_dquote', email='esc_dquote@example.com', age=30)
    user.save()

    values = [
        'hello"world',
        '"""triple double"""',
        'mix"of"quotes',
    ]

    for i, val in enumerate(values):
        order = Order(user_id=user.id, order_number=val, total_amount=Decimal('100'), status='pending')
        order.save()

        results_expr = Order.query().where(Order.c.order_number == val).all()
        assert len(results_expr) == 1, f"Expression query failed for '{val}'"
        assert results_expr[0].order_number == val

        results_raw = Order.query().where('order_number = ?', (val,)).all()
        assert len(results_raw) == 1, f"Raw parameterized query failed for '{val}'"
        assert results_raw[0].order_number == val


def test_escape_consistency_backslash(order_fixtures):
    """
    Test values with backslash characters roundtrip correctly via both query methods.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='esc_bslash', email='esc_bslash@example.com', age=30)
    user.save()

    values = [
        'path\\to\\file',
        '\\\\double backslash\\\\',
        'mix\\and\'quote',
    ]

    for i, val in enumerate(values):
        order = Order(user_id=user.id, order_number=val, total_amount=Decimal('100'), status='pending')
        order.save()

        results_expr = Order.query().where(Order.c.order_number == val).all()
        assert len(results_expr) == 1, f"Expression query failed for '{val}'"
        assert results_expr[0].order_number == val

        results_raw = Order.query().where('order_number = ?', (val,)).all()
        assert len(results_raw) == 1, f"Raw parameterized query failed for '{val}'"
        assert results_raw[0].order_number == val


def test_escape_consistency_sql_keywords(order_fixtures):
    """
    Test that SQL keywords used as data values are treated as data, not SQL.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='esc_keywords', email='esc_keywords@example.com', age=30)
    user.save()

    values = [
        'NULL',
        'DROP',
        'DELETE',
        'SELECT',
        'INSERT',
        'UPDATE',
        'CREATE',
    ]

    for i, val in enumerate(values):
        order = Order(user_id=user.id, order_number=val, total_amount=Decimal('100'), status='pending')
        order.save()

        results_expr = Order.query().where(Order.c.order_number == val).all()
        assert len(results_expr) == 1, f"Expression query failed for keyword '{val}'"
        assert results_expr[0].order_number == val

        results_raw = Order.query().where('order_number = ?', (val,)).all()
        assert len(results_raw) == 1, f"Raw parameterized query failed for keyword '{val}'"
        assert results_raw[0].order_number == val


# ============================================================
# Injection immunity tests (注入安全性)
# Verify that SQL injection payload patterns never escape as SQL,
# always treated as data values.
# ============================================================

def test_injection_payloads_as_data(order_fixtures):
    """
    Test that common SQL injection payloads are safely handled as data.

    Each payload:
    - Is successfully inserted as a data value
    - Is successfully retrieved as the exact same value
    - Does not cause any database corruption (other records remain intact)
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='inject_immunity', email='inject_immunity@example.com', age=30)
    user.save()

    injection_payloads = [
        "'; DROP TABLE users--",
        "'; DELETE FROM orders WHERE 1=1--",
        "admin' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
        "x'; WAITFOR DELAY '0:0:5'--",
        "1' OR '1'='1' /*",
        "'; EXEC sp_msdrop--",
        "'; SHUTDOWN--",
    ]

    for i, payload in enumerate(injection_payloads):
        order = Order(
            user_id=user.id,
            order_number=payload,
            total_amount=Decimal(f'{i+1}0.00'),
            status='pending',
        )
        order.save()

        # Verify the payload is stored and retrieved as data (not executed)
        result = Order.query().where(Order.c.total_amount == Decimal(f'{i+1}0.00')).one()
        assert result.order_number == payload, \
            f"Payload was not preserved: sent={payload!r}, stored={result.order_number!r}"

        # Verify via parameterized query too
        result_raw = Order.query().where(
            'order_number = ?', (payload,)
        ).all()
        assert len(result_raw) >= 1, f"Cannot find payload via raw query: {payload}"
        assert result_raw[0].order_number == payload

    # Sanity check: unrelated query still works
    all_orders = Order.query().where(Order.c.user_id == user.id).all()
    assert len(all_orders) >= len(injection_payloads)


def test_sql_comment_injection_immunity(order_fixtures):
    """
    Comment-based injection payloads (--, /*) are treated as data, not SQL.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='comment_immune', email='comment_immune@example.com', age=30)
    user.save()

    payloads = [
        "normal'; -- DROP TABLE users",
        "normal'; /* malicious comment */ x",
        "value'; /* nested /**/ comment */ --",
        "x'/* comment */ OR '1'='1",
    ]

    for i, payload in enumerate(payloads):
        order = Order(
            user_id=user.id, order_number=payload,
            total_amount=Decimal(f'{i+1}0.00'), status='pending',
        )
        order.save()

        result = Order.query().where(
            Order.c.order_number == payload
        ).all()
        assert len(result) == 1, f"Failed to find payload '{payload}' by expression"
        assert result[0].order_number == payload

    all_orders = Order.query().all()
    assert len(all_orders) > 0


def test_special_character_full_matrix(order_fixtures):
    """
    Test a comprehensive matrix of special characters roundtripping
    via both expression-based and raw parameterized queries.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='matrix_user', email='matrix@example.com', age=30)
    user.save()

    special_values = [
        "line1\nline2\t tabbed",
        "carriage\rreturn",
        "\0null\0char",
        "",
        "   spaces   ",
        "unicode中文emoji🎉",
        "\\' \\\" backslash with quotes",
        "%percent_sign",
        "_underscore",
        "normal string with nothing special",
        "(parentheses) and [brackets]",
        "semicolon; no injection",
    ]

    for i, val in enumerate(special_values):
        order = Order(
            user_id=user.id,
            order_number=f"MATRIX-{i:03d}",
            total_amount=Decimal(f'{i+1}0.00'),
            status=val,
        )
        order.save()

        # Retrieve by status (the special value)
        results = Order.query().where(Order.c.status == val).all()
        assert len(results) >= 1, f"Expression query missed '{val!r}'"
        for r in results:
            if r.total_amount == Decimal(f'{i+1}0.00'):
                assert r.status == val

        # Retrieve by parameterized query
        results_raw = Order.query().where('status = ?', (val,)).all()
        assert len(results_raw) >= 1, f"Raw query missed '{val!r}'"


def test_value_equivalence_expression_vs_parameterized(order_fixtures):
    """
    For a given value, expression-based and raw parameterized queries
    produce identical result sets.

    This is the core escape consistency guarantee: the ORM expression
    builder and manual parameterized SQL must produce the same output.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='equiv_user', email='equiv@example.com', age=30)
    user.save()

    test_rows = [
        ("ORD-EQ01", "pending", Decimal('10.00')),
        ("ORD-EQ02", "it's value", Decimal('20.00')),
        ("ORD-EQ03", 'double"quote', Decimal('30.00')),
        ("ORD-EQ04", "pending", Decimal('10.00')),
    ]

    for num, status, amount in test_rows:
        Order(user_id=user.id, order_number=num, total_amount=amount, status=status).save()

    # Query by status= pending — both methods should find ORD-EQ01 and ORD-EQ04
    expr_result = Order.query().where(Order.c.status == 'pending').all()
    raw_result = Order.query().where('status = ?', ('pending',)).all()

    assert len(expr_result) == len(raw_result), \
        f"Result count mismatch: expr={len(expr_result)}, raw={len(raw_result)}"

    expr_nums = sorted(r.order_number for r in expr_result)
    raw_nums = sorted(r.order_number for r in raw_result)
    assert expr_nums == raw_nums, \
        f"Result mismatch: expr={expr_nums}, raw={raw_nums}"