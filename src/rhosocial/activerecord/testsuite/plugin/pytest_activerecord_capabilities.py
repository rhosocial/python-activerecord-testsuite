"""
Pytest plugin for Active Record capability checking.

This plugin provides automatic capability checking for tests that use
the @requires_capability decorator. It ensures that tests are skipped
if the current backend doesn't support the required capabilities.
"""

import pytest


def pytest_configure(config):
    """Configure the plugin."""
    # Add marker for documentation
    config.addinivalue_line(
        "markers", 
        "requires_capability: Mark tests that require specific database capabilities"
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item):
    """
    Hook that runs during test execution to check capability requirements.
    
    This hook intercepts tests with requires_capability markers and
    checks if the current backend supports the required capabilities.
    If not, the test is skipped.
    """
    # Check if the test has a requires_capability marker
    requires_capability_marker = item.get_closest_marker("requires_capability")
    if requires_capability_marker:
        required_capabilities = requires_capability_marker.args[0]
        
        # Access the fixture values that are available at test execution time
        # They are in item.funcargs at this point
        if hasattr(item, 'funcargs'):
            # Find a fixture that contains a model with backend access
            model_to_check = None
            
            # Check for values in funcargs (fixtures available to the test)
            for fixture_name, fixture_value in item.funcargs.items():
                try:
                    # Handle different types of fixture returns
                    if isinstance(fixture_value, tuple):
                        # If it's a tuple of models, use the first one that has backend access
                        for model in fixture_value:
                            if hasattr(model, 'backend') or hasattr(model, '__backend__'):
                                model_to_check = model
                                break
                    elif hasattr(fixture_value, 'backend') or hasattr(fixture_value, '__backend__'):
                        # If it's a single model/class with backend access
                        model_to_check = fixture_value
                    elif hasattr(fixture_value, '__getitem__') and len(fixture_value) > 0:
                        # If it's an array-like structure
                        first_item = fixture_value[0] 
                        if hasattr(first_item, 'backend') or hasattr(first_item, '__backend__'):
                            model_to_check = first_item
                            
                    if model_to_check is not None:
                        break
                except Exception as e:
                    # Log the exception to help debug why some tests aren't being skipped
                    import traceback
                    print(f"DEBUG: Exception when accessing fixture '{fixture_name}' in test '{item.name}': {e}")
                    print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
                    # If we can't get the fixture value, continue to the next option
                    continue
            
            if model_to_check is not None:
                if hasattr(model_to_check, 'backend') or hasattr(model_to_check, '__backend__'):
                    try:
                        # Use the model to check capabilities
                        _check_and_skip_if_unsupported(model_to_check, required_capabilities)
                    except Exception as e:
                        # Log exception during capability check
                        print(f"DEBUG: Exception during capability check for test '{item.name}': {e}")
                        # Re-raise the exception to ensure failures are visible
                        raise
                else:
                    # Log when model doesn't have the expected backend attributes
                    print(f"DEBUG: Model {model_to_check} doesn't have expected backend attributes in test '{item.name}'")
                    print(f"DEBUG: Available attributes: {[attr for attr in dir(model_to_check) if not attr.startswith('_')]}")
            else:
                # Log when no model with backend was found
                print(f"DEBUG: No model with backend access found for test '{item.name}'")
                print(f"DEBUG: Available fixtures: {list(item.funcargs.keys()) if hasattr(item, 'funcargs') else 'N/A'}")


def _check_and_skip_if_unsupported(model_class, capability_info):
    """
    Check if backend supports required capabilities, skip test if not.
    
    This function is a modified version of skip_test_if_capability_unsupported
    from utils.py, adjusted for use in the plugin context.
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
    backend = model_class.backend()
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