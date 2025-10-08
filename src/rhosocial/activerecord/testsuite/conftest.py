# src/rhosocial/activerecord/testsuite/conftest.py
"""
This file serves as the root pytest configuration for the entire testsuite package.
Its purpose is to define global configurations and hooks for pytest, such as
registering custom markers that can be used to categorize and filter tests.
"""
import os
import pytest
import warnings

# Set the environment variable that the testsuite uses to locate the provider registry.
# The testsuite is a generic package and doesn't know the specific location of the
# provider implementations for this backend (SQLite). This environment variable
# acts as a bridge, pointing the testsuite to the correct import path.
#
# `setdefault` is used to ensure that this value is set only if it hasn't been
# set already, allowing for overrides in different environments if needed.
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'providers.registry:provider_registry'
)


def pytest_configure(config):
    """
    A pytest hook that runs at the beginning of a test session to configure
    the test environment.
    """
    # Register custom markers to allow for selective test runs.
    # For example, `pytest -m feature` will run only the core feature tests.
    config.addinivalue_line("markers", "requires_capability: Mark tests that require specific database capabilities")

def pytest_collection_modifyitems(config, items):
    """
    Hook to automatically skip tests that require unsupported capabilities.
    
    Note: During collection time, we can't access backend-specific capabilities
    through the provider interface since providers set up backends per test scenario.
    Capability checking happens during test execution when provider-configured
    models are available.
    """
    # For now, we just ensure tests with requires_capability markers exist properly
    # Actual capability checking occurs at test runtime via fixtures and decorators
    pass

def pytest_sessionstart(session):
    """
    Hook to generate capability support warnings at session start.
    
    This hook generates warnings about important unsupported capabilities
    to alert developers about backend limitations.
    """
    try:
        # Import required capability classes
        from rhosocial.activerecord.backend.capabilities import (
            CapabilityCategory,
            AdvancedGroupingCapability,
            CTECapability,
            ReturningCapability,
            WindowFunctionCapability
        )
        
        # Get current backend
        from .utils import get_current_backend
        backend = get_current_backend()
        
        # Generate warnings for important unsupported capabilities
        capabilities = backend.capabilities
        
        unsupported_important_capabilities = []
        
        # Check for important capabilities
        if not capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS):
            unsupported_important_capabilities.append("Window Functions")
        
        if not capabilities.supports_advanced_grouping(AdvancedGroupingCapability.CUBE):
            unsupported_important_capabilities.append("CUBE Grouping")
        
        if not capabilities.supports_advanced_grouping(AdvancedGroupingCapability.ROLLUP):
            unsupported_important_capabilities.append("ROLLUP Grouping")
        
        if not capabilities.supports_cte(CTECapability.BASIC_CTE):
            unsupported_important_capabilities.append("Common Table Expressions")
        
        if not capabilities.supports_returning(ReturningCapability.BASIC_RETURNING):
            unsupported_important_capabilities.append("RETURNING Clause")
        
        if unsupported_important_capabilities:
            warnings.warn(
                f"Current backend does not support important capabilities: "
                f"{', '.join(unsupported_important_capabilities)}. "
                f"Some tests will be automatically skipped.",
                UserWarning
            )
    except Exception as e:
        # If we can't determine capability support, continue normally
        warnings.warn(f"Could not check capability support at session start: {e}", UserWarning)