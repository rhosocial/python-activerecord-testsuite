# src/rhosocial/activerecord/testsuite/utils.py
"""
Utility functions for the testsuite package.

This module provides:
1. Capability checking decorators for marking test requirements
2. Runtime capability validation functions
3. Convenience decorators for common capability requirements

All tests across the entire testsuite should import capability utilities from this module.
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
    # The real capability checking should happen at test execution time
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
# Capability Checking Functions
# ============================================================================

def skip_test_if_capability_unsupported(model_class, capability_info):
    """
    Skip the current test if the backend doesn't support the required capability.

    This function is called during test execution when we have access to
    the provider-configured model and can check its backend capabilities.

    Args:
        model_class: A provider-configured model class
        capability_info: A tuple of (capability_category, specific_capability)
                        where specific_capability can be:
                        - None: check for category support only
                        - Single capability: check for that specific capability
                        - List of capabilities: check all are supported

    Raises:
        pytest.skip: If required capabilities are not supported
        ValueError: If capability_info format is invalid
    """
    # Import required capability classes
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        SetOperationCapability,
        WindowFunctionCapability,
        AdvancedGroupingCapability,
        CTECapability,
        JSONCapability,
        ReturningCapability,
        TransactionCapability,
        BulkOperationCapability,
        JoinCapability,
        ConstraintCapability,
        AggregateFunctionCapability,
        DateTimeFunctionCapability,
        StringFunctionCapability,
        MathematicalFunctionCapability
    )

    # Get the backend from the model
    backend = get_backend_from_model(model_class)
    capabilities = backend.capabilities

    # Expect a tuple of (capability_category, specific_capability)
    if not isinstance(capability_info, tuple) or len(capability_info) != 2:
        raise ValueError(
            "capability_info must be a tuple of (capability_category, specific_capability). "
            f"Got: {capability_info}"
        )

    capability_category, specific_capability = capability_info

    if specific_capability is None:
        # Only check for category support
        if not capabilities.supports_category(capability_category):
            pytest.skip(
                f"Skipping test - unsupported capability category: {capability_category.name}"
            )
    else:
        # Check for specific capability within category
        unsupported_capabilities = []

        # Ensure specific_capability is a list for consistent processing
        if not isinstance(specific_capability, list):
            specific_capability = [specific_capability]

        # Determine the appropriate check method based on category
        for spec_cap in specific_capability:
            check_result = False

            # Map category to appropriate support checking method
            if capability_category == CapabilityCategory.SET_OPERATIONS and isinstance(spec_cap,
                                                                                       SetOperationCapability):
                check_result = capabilities.supports_set_operation(spec_cap)
            elif capability_category == CapabilityCategory.WINDOW_FUNCTIONS and isinstance(spec_cap,
                                                                                           WindowFunctionCapability):
                check_result = capabilities.supports_window_function(spec_cap)
            elif capability_category == CapabilityCategory.ADVANCED_GROUPING and isinstance(spec_cap,
                                                                                            AdvancedGroupingCapability):
                check_result = capabilities.supports_advanced_grouping(spec_cap)
            elif capability_category == CapabilityCategory.CTE and isinstance(spec_cap, CTECapability):
                check_result = capabilities.supports_cte(spec_cap)
            elif capability_category == CapabilityCategory.JSON_OPERATIONS and isinstance(spec_cap, JSONCapability):
                check_result = capabilities.supports_json(spec_cap)
            elif capability_category == CapabilityCategory.RETURNING_CLAUSE and isinstance(spec_cap,
                                                                                           ReturningCapability):
                check_result = capabilities.supports_returning(spec_cap)
            elif capability_category == CapabilityCategory.TRANSACTION_FEATURES and isinstance(spec_cap,
                                                                                               TransactionCapability):
                check_result = capabilities.supports_transaction(spec_cap)
            elif capability_category == CapabilityCategory.BULK_OPERATIONS and isinstance(spec_cap,
                                                                                          BulkOperationCapability):
                check_result = capabilities.supports_bulk_operation(spec_cap)
            elif capability_category == CapabilityCategory.JOIN_OPERATIONS and isinstance(spec_cap, JoinCapability):
                check_result = capabilities.supports_join_operation(spec_cap)
            elif capability_category == CapabilityCategory.CONSTRAINTS and isinstance(spec_cap, ConstraintCapability):
                check_result = capabilities.supports_constraint(spec_cap)
            elif capability_category == CapabilityCategory.AGGREGATE_FUNCTIONS and isinstance(spec_cap,
                                                                                              AggregateFunctionCapability):
                check_result = capabilities.supports_aggregate_function(spec_cap)
            elif capability_category == CapabilityCategory.DATETIME_FUNCTIONS and isinstance(spec_cap,
                                                                                             DateTimeFunctionCapability):
                check_result = capabilities.supports_datetime_function(spec_cap)
            elif capability_category == CapabilityCategory.STRING_FUNCTIONS and isinstance(spec_cap,
                                                                                           StringFunctionCapability):
                check_result = capabilities.supports_string_function(spec_cap)
            elif capability_category == CapabilityCategory.MATHEMATICAL_FUNCTIONS and isinstance(spec_cap,
                                                                                                 MathematicalFunctionCapability):
                check_result = capabilities.supports_mathematical_function(spec_cap)

            if not check_result:
                unsupported_capabilities.append(str(spec_cap))

        if unsupported_capabilities:
            pytest.skip(
                f"Skipping test - unsupported capabilities: {', '.join(unsupported_capabilities)}"
            )


# ============================================================================
# Capability Requirement Decorators
# ============================================================================

def requires_capability(capability_category, specific_capability=None):
    """
    Decorator to mark a test function as requiring specific database capabilities.

    This decorator should be used by ALL tests in the testsuite that require
    specific database features. The actual capability checking happens at runtime
    via the check_capability_requirements fixture in conftest.py.

    Args:
        capability_category: The top-level capability category (e.g., CapabilityCategory.SET_OPERATIONS)
        specific_capability: The specific capability within the category, which can be:
                           - None: requires any capability in the category
                           - Single capability enum: requires that specific capability
                           - List of capability enums: requires all listed capabilities

    Returns:
        pytest.mark.requires_capability decorator that will be processed by conftest.py

    Examples:
        # Category-level requirement (any capability in category)
        @requires_capability(CapabilityCategory.SET_OPERATIONS)
        def test_set_operations(fixtures):
            pass

        # Specific capability requirement
        @requires_capability(CapabilityCategory.SET_OPERATIONS, SetOperationCapability.UNION)
        def test_union(fixtures):
            pass

        # Multiple specific capabilities
        @requires_capability(
            CapabilityCategory.SET_OPERATIONS,
            [SetOperationCapability.UNION, SetOperationCapability.INTERSECT]
        )
        def test_union_intersect(fixtures):
            pass
    """
    return pytest.mark.requires_capability((capability_category, specific_capability))


# ============================================================================
# Convenience Decorators for Common Capabilities
# ============================================================================

def requires_window_functions(specific_functions=None):
    """
    Decorator for tests requiring window functions.

    Args:
        specific_functions: Optional list of specific window functions required.
                          If None, requires any window function support.

    Examples:
        @requires_window_functions()
        def test_any_window_function(fixtures):
            pass

        @requires_window_functions([WindowFunctionCapability.ROW_NUMBER, WindowFunctionCapability.RANK])
        def test_ranking_functions(fixtures):
            pass
    """
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        WindowFunctionCapability
    )

    if specific_functions is None:
        # Require at least basic window function support
        specific_functions = WindowFunctionCapability.ROW_NUMBER

    return requires_capability(CapabilityCategory.WINDOW_FUNCTIONS, specific_functions)

def requires_cube():
    """Decorator for tests requiring CUBE grouping."""
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        AdvancedGroupingCapability
    )
    return requires_capability(CapabilityCategory.ADVANCED_GROUPING, AdvancedGroupingCapability.CUBE)

def requires_rollup():
    """Decorator for tests requiring ROLLUP grouping."""
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        AdvancedGroupingCapability
    )
    return requires_capability(CapabilityCategory.ADVANCED_GROUPING, AdvancedGroupingCapability.ROLLUP)

def requires_grouping_sets():
    """Decorator for tests requiring GROUPING SETS grouping."""
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        AdvancedGroupingCapability
    )
    return requires_capability(CapabilityCategory.ADVANCED_GROUPING, AdvancedGroupingCapability.GROUPING_SETS)

def requires_cte():
    """Decorator for tests requiring Common Table Expressions."""
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        CTECapability
    )
    return requires_capability(CapabilityCategory.CTE, CTECapability.BASIC_CTE)

def requires_recursive_cte():
    """Decorator for tests requiring recursive CTEs."""
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        CTECapability
    )
    return requires_capability(CapabilityCategory.CTE, CTECapability.RECURSIVE_CTE)

def requires_json_operations(specific_operations=None):
    """
    Decorator for tests requiring JSON operations.

    Args:
        specific_operations: Optional list of specific JSON operations required.
                           If None, requires any JSON operation support.
    """
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        JSONCapability
    )

    if specific_operations is None:
        # Require at least basic JSON extraction
        specific_operations = JSONCapability.JSON_EXTRACT

    return requires_capability(CapabilityCategory.JSON_OPERATIONS, specific_operations)

def requires_returning_clause():
    """Decorator for tests requiring RETURNING clause."""
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        ReturningCapability
    )
    return requires_capability(CapabilityCategory.RETURNING_CLAUSE, ReturningCapability.BASIC_RETURNING)

def requires_set_operations(specific_operations=None):
    """
    Decorator for tests requiring set operations (UNION, INTERSECT, EXCEPT).

    Args:
        specific_operations: Optional list of specific set operations required.
                           If None, requires any set operation support.
    """
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        SetOperationCapability
    )

    if specific_operations is None:
        # Require at least UNION support
        specific_operations = SetOperationCapability.UNION

    return requires_capability(CapabilityCategory.SET_OPERATIONS, specific_operations)

def requires_bulk_operations(specific_operations=None):
    """
    Decorator for tests requiring bulk operations.

    Args:
        specific_operations: Optional list of specific bulk operations required.
                           If None, requires any bulk operation support.
    """
    from rhosocial.activerecord.backend.capabilities import (
        CapabilityCategory,
        BulkOperationCapability
    )

    if specific_operations is None:
        specific_operations = BulkOperationCapability.BULK_INSERT

    return requires_capability(CapabilityCategory.BULK_OPERATIONS, specific_operations)


# ============================================================================
# Pytest Hook for Capability Checking
# ============================================================================




# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Backend access
    'get_current_backend',
    'get_backend_from_model',

    # Capability checking
    'skip_test_if_capability_unsupported',

    # Decorators
    'requires_capability',

    # Convenience decorators
    'requires_window_functions',
    'requires_cube',
    'requires_rollup',
    'requires_grouping_sets',
    'requires_cte',
    'requires_recursive_cte',
    'requires_json_operations',
    'requires_returning_clause',
    'requires_set_operations',
    'requires_bulk_operations',
]