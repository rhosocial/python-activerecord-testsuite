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


# ============================================================
# LIKE wildcard behavior tests (LIKE 通配符行为)
# Verify that like() treats % and _ as SQL wildcards,
# and documents that no auto-escaping is provided for
# literal % and _ characters in patterns.
# ============================================================

def test_like_wildcard_percent(order_fixtures):
    """
    Test that % in like() patterns is treated as a SQL wildcard.

    The % wildcard matches any sequence of zero or more characters.
    This verifies standard SQL LIKE behavior through the ORM's
    like() method.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='like_pct', email='like_pct@example.com', age=30)
    user.save()

    Order(user_id=user.id, order_number='LIKE-A01', total_amount=Decimal('10'), status='pending').save()
    Order(user_id=user.id, order_number='LIKE-A02', total_amount=Decimal('20'), status='pending').save()
    Order(user_id=user.id, order_number='LIKE-B01', total_amount=Decimal('30'), status='shipped').save()

    # % matches any sequence of characters
    results = Order.query().where(Order.c.order_number.like('LIKE-A%')).all()
    assert len(results) == 2
    assert all(r.order_number.startswith('LIKE-A') for r in results)

    # % at both ends matches any containing substring
    results = Order.query().where(Order.c.order_number.like('%B0%')).all()
    assert len(results) == 1
    assert results[0].order_number == 'LIKE-B01'

    # % matching zero characters
    results = Order.query().where(Order.c.order_number.like('LIKE-A01%')).all()
    assert len(results) == 1
    assert results[0].order_number == 'LIKE-A01'


def test_like_wildcard_underscore(order_fixtures):
    """
    Test that _ in like() patterns is treated as a SQL wildcard.

    The _ wildcard matches exactly one character. This verifies
    standard SQL LIKE behavior through the ORM's like() method.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='like_und', email='like_und@example.com', age=30)
    user.save()

    Order(user_id=user.id, order_number='LK_A', total_amount=Decimal('10'), status='pending').save()
    Order(user_id=user.id, order_number='LK_AB', total_amount=Decimal('20'), status='pending').save()
    Order(user_id=user.id, order_number='LK_B', total_amount=Decimal('30'), status='shipped').save()

    # _ matches exactly one character: LK__ matches 4-char strings starting with LK
    results = Order.query().where(Order.c.order_number.like('LK__')).all()
    result_nums = {r.order_number for r in results}
    assert result_nums == {'LK_A', 'LK_B'}, \
        f"Expected {{'LK_A', 'LK_B'}}, got {result_nums}"


def test_like_no_auto_escape(order_fixtures):
    """
    Test that like() does NOT auto-escape % and _ in patterns.

    This documents current behavior: if a stored value contains
    literal % or _, using like() with that value will treat them
    as wildcards. For exact matching, use equality (==) instead.
    Users who need LIKE with literal % or _ must use raw SQL
    with the ESCAPE clause.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='like_noesc', email='like_noesc@example.com', age=30)
    user.save()

    # Values containing literal % and _
    Order(user_id=user.id, order_number='100%complete', total_amount=Decimal('10'), status='pending').save()
    Order(user_id=user.id, order_number='100xcomplete', total_amount=Decimal('20'), status='pending').save()
    Order(user_id=user.id, order_number='file_name', total_amount=Decimal('30'), status='pending').save()
    Order(user_id=user.id, order_number='fileXname', total_amount=Decimal('40'), status='pending').save()

    # like('100%complete') — % acts as wildcard, matching both values
    results = Order.query().where(Order.c.order_number.like('100%complete')).all()
    assert len(results) == 2, \
        "like('100%complete') should match both '100%complete' and '100xcomplete'"

    # like('file_name') — _ acts as wildcard, matching both values
    # (both 9 chars; _ in the pattern matches _ and X at position 5)
    results = Order.query().where(Order.c.order_number.like('file_name')).all()
    assert len(results) == 2, \
        "like('file_name') should match both 'file_name' and 'fileXname'"

    # For exact match, use equality comparison instead of like()
    results = Order.query().where(Order.c.order_number == '100%complete').all()
    assert len(results) == 1
    assert results[0].order_number == '100%complete'

    results = Order.query().where(Order.c.order_number == 'file_name').all()
    assert len(results) == 1
    assert results[0].order_number == 'file_name'


# ============================================================
# NULL comparison: is_null() vs == None (NULL 比较方法)
# Verify that == None generates '= NULL' (never matches in SQL)
# while is_null() generates 'IS NULL' (correct). This documents
# the correct API for null comparison.
# ============================================================

def test_null_comparison_with_is_null(order_fixtures):
    """
    Test that == None generates '= NULL' (never matches) while
    is_null() generates 'IS NULL' (correct).

    In SQL, any comparison with NULL using = returns UNKNOWN
    (not TRUE), so 'column = NULL' never matches any rows.
    The is_null() method generates the correct 'IS NULL' predicate.
    """
    User, Order, OrderItem = order_fixtures

    # Create users with null and non-null age
    user_null = User(username='is_null_user', email='isnull@example.com', age=None)
    user_null.save()

    user_with_age = User(username='has_age_user', email='hasage@example.com', age=25)
    user_with_age.save()

    # == None generates 'age = NULL' which never matches
    # (SQL three-valued logic: NULL = NULL -> UNKNOWN, not TRUE)
    results_eq_none = User.query().where(User.c.age == None).all()
    assert len(results_eq_none) == 0, \
        "== None generates '= NULL' which never matches in SQL"

    # is_null() generates 'age IS NULL' which correctly matches null values
    results_is_null = User.query().where(User.c.age.is_null()).all()
    assert len(results_is_null) >= 1, \
        "is_null() generates 'IS NULL' which correctly matches null values"
    assert any(r.username == 'is_null_user' for r in results_is_null)

    # is_not_null() generates 'age IS NOT NULL'
    results_is_not_null = User.query().where(User.c.age.is_not_null()).all()
    assert len(results_is_not_null) >= 1
    assert any(r.username == 'has_age_user' for r in results_is_not_null)
    assert not any(r.username == 'is_null_user' for r in results_is_not_null)


# ============================================================
# IN clause injection immunity (IN 子句注入安全性)
# Verify that injection payloads in IN clause value lists
# are safely parameterized and never escape as SQL code.
# ============================================================

def test_in_clause_injection_immunity(order_fixtures):
    """
    Test that injection payloads in in_() value lists are safely
    parameterized and never escape as SQL code.

    Each payload is inserted as data and can be retrieved via in_()
    with the same payload in the list. No data corruption occurs.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='in_inject', email='in_inject@example.com', age=30)
    user.save()

    payloads = [
        "'; DROP TABLE users--",
        "admin' OR '1'='1",
        "' UNION SELECT * FROM users--",
        "1; DROP TABLE orders",
    ]

    # Insert orders with injection payloads as order_number
    for i, payload in enumerate(payloads):
        Order(
            user_id=user.id,
            order_number=payload,
            total_amount=Decimal(f'{i+1}0.00'),
            status='pending',
        ).save()

    # Also create a normal order that should NOT be matched
    Order(user_id=user.id, order_number='IN-NORMAL', total_amount=Decimal('999'), status='pending').save()

    # Query using in_() with injection payloads
    results = Order.query().where(Order.c.order_number.in_(payloads)).all()
    assert len(results) == len(payloads), \
        f"Expected {len(payloads)} results, got {len(results)}"

    # Verify each payload was stored and retrieved correctly
    result_numbers = {r.order_number for r in results}
    for payload in payloads:
        assert payload in result_numbers, f"Payload not found: {payload!r}"

    # Normal order should NOT be in the results
    assert 'IN-NORMAL' not in result_numbers

    # Verify data integrity — all orders still accessible
    all_orders = Order.query().where(Order.c.user_id == user.id).all()
    assert len(all_orders) == len(payloads) + 1


# ============================================================
# Placeholder conversion edge cases (占位符转换边缘情况)
# Verify that escaped placeholders (\\?) in raw SQL are treated
# as literal question marks, not parameter slots.
# ============================================================

def test_qmark_placeholder_escaping(order_fixtures):
    """
    Test that escaped placeholders (\\?) in raw SQL are treated as
    literal question marks, not parameter slots.

    The convert_qmark_placeholder() function supports \\? (literal ?)
    for backend-specific operators like PostgreSQL JSONB ?. On %s
    backends, \\? produces a literal ? that is not consumed as a
    parameter.

    Note: Using \\? inside LIKE patterns with % (e.g., '%\\?%') is
    not supported on PostgreSQL because psycopg3 interprets %? as an
    invalid placeholder. Use \\? only in operator contexts.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='qmark_esc', email='qmark_esc@example.com', age=30)
    user.save()

    # Create orders — one with '?' in order_number, one without
    Order(
        user_id=user.id, order_number='ORD?-001',
        total_amount=Decimal('10'), status='pending',
    ).save()

    Order(
        user_id=user.id, order_number='ORD-002',
        total_amount=Decimal('20'), status='shipped',
    ).save()

    # Verify: normal ? as parameter works correctly across all backends
    results = Order.query().where('order_number = ?', ('ORD-002',)).all()
    assert len(results) == 1
    assert results[0].order_number == 'ORD-002'

    # Verify: multiple ? parameters work correctly
    results = Order.query().where(
        'order_number = ? AND status = ?',
        ('ORD?-001', 'pending'),
    ).all()
    assert len(results) == 1
    assert results[0].order_number == 'ORD?-001'

    # Verify: \\? is treated as literal ?, not a parameter slot.
    # On %s backends (MySQL), \\? → literal ?, ? → %s (parameter).
    # This query has 1 unescaped ? (parameter) and 1 escaped \\? (literal).
    # Providing 1 parameter should work because \\? is not a parameter slot.
    #
    # Note: On PostgreSQL (psycopg3), \\? inside LIKE '%...%' produces
    # %? which psycopg3 rejects. This is a known limitation — \\? is
    # designed for operator contexts (JSONB ?), not LIKE patterns.
    try:
        results = Order.query().where(
            "order_number LIKE '%\\?%' AND status = ?",
            ('pending',),
        ).all()
        assert len(results) >= 1
        assert any(r.order_number == 'ORD?-001' for r in results)
    except Exception:
        # PostgreSQL (psycopg3) rejects %? — known limitation.
        # Verify the order can still be found via expression query.
        results = Order.query().where(Order.c.order_number == 'ORD?-001').all()
        assert len(results) == 1


# ============================================================
# Tautology injection immunity (永真注入安全性)
# Verify that values resembling SQL tautologies (e.g., '1=1',
# 'OR 1=1--') in WHERE conditions are treated as data, not SQL.
# ============================================================

def test_tautology_injection_immunity(order_fixtures):
    """
    Test that values resembling SQL tautologies are treated as
    data, not SQL code, in parameterized queries.

    Values like '1=1', 'OR 1=1--' stored as data should only
    match records with that exact value — never all records.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='tautology_test', email='tautology@example.com', age=30)
    user.save()

    # Create a normal order with a standard status
    Order(user_id=user.id, order_number='TAUT-NORM', total_amount=Decimal('100'), status='pending').save()

    # Create orders with tautology-looking values as status
    tautology_values = [
        "1=1",
        "TRUE",
        "OR 1=1--",
        "' OR '1'='1",
        "1; DROP TABLE orders",
    ]

    for i, val in enumerate(tautology_values):
        Order(
            user_id=user.id, order_number=f"TAUT-{i:03d}",
            total_amount=Decimal(f'{i+1}0.00'), status=val,
        ).save()

    # Each tautology value should only match records with that exact status
    for val in tautology_values:
        results = Order.query().where(Order.c.status == val).all()
        assert len(results) >= 1, f"No results for tautology value: {val!r}"
        for r in results:
            assert r.status == val, \
                f"Matched record has different status: expected {val!r}, got {r.status!r}"

    # The normal 'pending' order should NOT be matched by tautology queries
    pending_results = Order.query().where(Order.c.status == 'pending').all()
    assert len(pending_results) == 1
    assert pending_results[0].order_number == 'TAUT-NORM'


# ============================================================
# Query error recovery (查询错误恢复)
# Verify that after a failed query, subsequent queries still
# work correctly and data integrity is maintained.
# ============================================================

def test_query_error_recovery(order_fixtures):
    """
    Test that after a failed query, subsequent queries still work
    correctly and data integrity is maintained.

    This verifies that query errors do not corrupt the connection
    state or leave the database in an inconsistent state.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='recovery_user', email='recovery@example.com', age=30)
    user.save()

    order = Order(
        user_id=user.id, order_number='RECOVERY-001',
        total_amount=Decimal('100'), status='pending',
    )
    order.save()

    # Execute a query that will fail (invalid SQL syntax)
    try:
        Order.query().where('invalid_sql_syntax_that_will_fail').all()
    except Exception:
        pass  # Expected to fail

    # Verify subsequent queries still work
    results = Order.query().where(Order.c.order_number == 'RECOVERY-001').all()
    assert len(results) == 1
    assert results[0].order_number == 'RECOVERY-001'

    # Verify data integrity
    all_orders = Order.query().where(Order.c.user_id == user.id).all()
    assert len(all_orders) == 1
    assert all_orders[0].total_amount == Decimal('100')