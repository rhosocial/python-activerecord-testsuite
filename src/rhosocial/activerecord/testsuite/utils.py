# src/rhosocial/activerecord/testsuite/utils.py
"""
Utility functions for the testsuite package.

This module provides:
1. Protocol checking decorators for marking test requirements
2. Runtime protocol validation functions
3. Convenience decorators for common protocol requirements

All tests across the entire testsuite should import protocol utilities from this module.
"""
import pytest


# ============================================================================
# Backend Access Functions
# ============================================================================

def get_current_backend():
    """
    Get the current database backend instance through the provider interface.

    This serves as a placeholder implementation. During the collection phase,
    we can't access the scenario-specific backends set up by the providers.
    This function returns None to allow collection to continue without crashing.

    Returns:
        None during collection phase, backend instance during execution
    """
    # For now, return None to allow collection to continue without crashing
    # The real protocol checking should happen at test execution time
    return None

def get_backend_from_model(model_class):
    """
    Get the backend instance from a model class.

    This function is used during test execution when we have access to
    provider-configured model classes.

    Args:
        model_class: A provider-configured model class

    Returns:
        Backend instance from the model class

    Raises:
        AttributeError: If model class doesn't have backend() method or __backend__ attribute
    """
    # Check for the correct backend access method according to IActiveRecord interface
    if hasattr(model_class, 'backend') and callable(getattr(model_class, 'backend')):
        # Use the class method approach as defined in IActiveRecord interface
        return model_class.backend()
    elif hasattr(model_class, '__backend__'):
        # Use the attribute approach as defined in IActiveRecord interface
        return model_class.__backend__
    else:
        raise AttributeError(
            f"Model class {model_class.__name__} doesn't have backend() method or __backend__ attribute. "
            f"Ensure it's properly configured by the provider according to IActiveRecord interface."
        )


# ============================================================================
# Protocol Checking Functions
# ============================================================================

def skip_test_if_protocol_unsupported(model_class, protocol_class, method_name=None):
    """
    Skip the current test if the backend doesn't support the required protocol.

    This function is called during test execution when we have access to
    the provider-configured model and can check its backend protocols.

    Args:
        model_class: A provider-configured model class
        protocol_class: The protocol class to check for (e.g., WindowFunctionSupport), or None for no specific protocol
        method_name: Optional specific method name to check for (e.g., 'supports_window_functions')

    Raises:
        pytest.skip: If required protocol is not supported
        ValueError: If protocol_class is not provided and not None (when no specific protocol is required)
    """
    if protocol_class is None:
        # If no specific protocol is required, just return without skipping
        return

    # Get the backend from the model
    backend = get_backend_from_model(model_class)

    # Check if backend implements the required protocol
    if not isinstance(backend.dialect, protocol_class):
        pytest.skip(
            f"Skipping test - backend dialect does not implement {protocol_class.__name__} protocol"
        )

    # If a specific method name is provided, check if it's supported
    if method_name:
        if hasattr(backend.dialect, method_name):
            method = getattr(backend.dialect, method_name)
            if callable(method):
                # For support checking methods that return bool, check if they return True
                if method_name.startswith('supports_'):
                    if not method():
                        pytest.skip(
                            f"Skipping test - backend dialect does not support {method_name.replace('supports_', '')}"
                        )


# ============================================================================
# Protocol Requirement Decorators
# ============================================================================

def requires_protocol(protocol_class, method_name=None):
    """
    Decorator to mark a test function as requiring specific database protocol support.

    This decorator should be used by ALL tests in the testsuite that require
    specific database features. The actual protocol checking happens at runtime
    via the check_protocol_requirements fixture in conftest.py.

    Args:
        protocol_class: The protocol class to check for (e.g., WindowFunctionSupport), or None for no specific protocol
        method_name: Optional specific method name to check for (e.g., 'supports_window_functions')

    Returns:
        pytest.mark.requires_protocol decorator that will be processed by conftest.py

    Examples:
        # Protocol-level requirement
        @requires_protocol(WindowFunctionSupport)
        def test_window_functions(fixtures):
            pass

        # Specific method requirement
        @requires_protocol(WindowFunctionSupport, 'supports_window_functions')
        def test_window_functions(fixtures):
            pass
    """
    return pytest.mark.requires_protocol((protocol_class, method_name))


# ============================================================================
# Convenience Decorators for Common Protocols
# ============================================================================

def requires_window_functions():
    """
    Decorator for tests requiring window function support.
    """
    from rhosocial.activerecord.backend.dialect.protocols import WindowFunctionSupport
    return requires_protocol(WindowFunctionSupport, 'supports_window_functions')

def requires_advanced_grouping():
    """Decorator for tests requiring advanced grouping operations (ROLLUP, CUBE, GROUPING SETS)."""
    from rhosocial.activerecord.backend.dialect.protocols import AdvancedGroupingSupport
    return requires_protocol(AdvancedGroupingSupport)

def requires_cube():
    """Decorator for tests requiring CUBE grouping."""
    from rhosocial.activerecord.backend.dialect.protocols import AdvancedGroupingSupport
    return requires_protocol(AdvancedGroupingSupport, 'supports_cube')

def requires_rollup():
    """Decorator for tests requiring ROLLUP grouping."""
    from rhosocial.activerecord.backend.dialect.protocols import AdvancedGroupingSupport
    return requires_protocol(AdvancedGroupingSupport, 'supports_rollup')

def requires_grouping_sets():
    """Decorator for tests requiring GROUPING SETS grouping."""
    from rhosocial.activerecord.backend.dialect.protocols import AdvancedGroupingSupport
    return requires_protocol(AdvancedGroupingSupport, 'supports_grouping_sets')

def requires_cte():
    """Decorator for tests requiring Common Table Expressions."""
    from rhosocial.activerecord.backend.dialect.protocols import CTESupport
    return requires_protocol(CTESupport, 'supports_basic_cte')

def requires_recursive_cte():
    """Decorator for tests requiring recursive CTEs."""
    from rhosocial.activerecord.backend.dialect.protocols import CTESupport
    return requires_protocol(CTESupport, 'supports_recursive_cte')

def requires_json_operations():
    """
    Decorator for tests requiring JSON operations.
    """
    from rhosocial.activerecord.backend.dialect.protocols import JSONSupport
    return requires_protocol(JSONSupport, 'supports_json_type')

def requires_returning_clause():
    """Decorator for tests requiring RETURNING clause."""
    from rhosocial.activerecord.backend.dialect.protocols import ReturningSupport
    return requires_protocol(ReturningSupport, 'supports_returning_clause')

def requires_set_operations():
    """
    Decorator for tests requiring set operations (UNION, INTERSECT, EXCEPT).
    """
    # Set operations are part of the core query functionality
    # Most backends support basic set operations
    # Since there isn't a specific SetOperationSupport protocol, we'll return a decorator
    # that doesn't require any specific protocol as basic set operations are typically supported by all backends
    return requires_protocol(None)  # No specific protocol required for basic set operations

def requires_lateral_joins():
    """Decorator for tests requiring LATERAL joins."""
    from rhosocial.activerecord.backend.dialect.protocols import LateralJoinSupport
    return requires_protocol(LateralJoinSupport, 'supports_lateral_join')

def requires_inner_join():
    """Decorator for tests requiring INNER JOIN support."""
    from rhosocial.activerecord.backend.dialect.protocols import JoinSupport
    return requires_protocol(JoinSupport, 'supports_inner_join')

def requires_left_join():
    """Decorator for tests requiring LEFT JOIN support."""
    from rhosocial.activerecord.backend.dialect.protocols import JoinSupport
    return requires_protocol(JoinSupport, 'supports_left_join')

def requires_cross_join():
    """Decorator for tests requiring CROSS JOIN support."""
    from rhosocial.activerecord.backend.dialect.protocols import JoinSupport
    return requires_protocol(JoinSupport, 'supports_cross_join')

def requires_natural_join():
    """Decorator for tests requiring NATURAL JOIN support."""
    from rhosocial.activerecord.backend.dialect.protocols import JoinSupport
    return requires_protocol(JoinSupport, 'supports_natural_join')

def requires_right_join():
    """Decorator for tests requiring RIGHT JOIN support (typically not supported by SQLite)."""
    from rhosocial.activerecord.backend.dialect.protocols import JoinSupport
    return requires_protocol(JoinSupport, 'supports_right_join')

def requires_full_join():
    """Decorator for tests requiring FULL JOIN support (typically not supported by SQLite)."""
    from rhosocial.activerecord.backend.dialect.protocols import JoinSupport
    return requires_protocol(JoinSupport, 'supports_full_join')

def requires_upsert():
    """Decorator for tests requiring UPSERT operations."""
    from rhosocial.activerecord.backend.dialect.protocols import UpsertSupport
    return requires_protocol(UpsertSupport, 'supports_upsert')

def requires_array_operations():
    """Decorator for tests requiring array operations."""
    from rhosocial.activerecord.backend.dialect.protocols import ArraySupport
    return requires_protocol(ArraySupport, 'supports_array_type')


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Backend access
    'get_current_backend',
    'get_backend_from_model',

    # Protocol checking
    'skip_test_if_protocol_unsupported',

    # Decorators
    'requires_protocol',

    # Convenience decorators
    'requires_window_functions',
    'requires_advanced_grouping',
    'requires_cube',
    'requires_rollup',
    'requires_grouping_sets',
    'requires_cte',
    'requires_recursive_cte',
    'requires_json_operations',
    'requires_inner_join',
    'requires_left_join',
    'requires_cross_join',
    'requires_natural_join',
    'requires_right_join',
    'requires_full_join',
    'requires_lateral_joins',
    'requires_upsert',
    'requires_array_operations',
    'requires_returning_clause',
    'requires_set_operations',
]