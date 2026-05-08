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
    config.addinivalue_line("markers", "requires_protocol: Mark tests that require specific database protocol support")
    config.addinivalue_line("markers", "requires_functions: Mark tests that require specific database functions")

def pytest_collection_modifyitems(config, items):
    """
    Hook to automatically skip tests that require unsupported protocols or functions.

    Note: During collection time, we can't access backend-specific capabilities
    through the provider interface since providers set up backends per test scenario.
    Protocol and function checking happens during test execution when provider-configured
    models are available.
    """
    # For now, we just ensure tests with requires_protocol/requires_functions markers exist properly
    # Actual capability checking occurs at test runtime via fixtures and decorators
    pass

def pytest_sessionstart(session):
    """
    Hook to generate capability support warnings at session start.
    
    This hook generates warnings about important unsupported capabilities
    to alert developers about backend limitations.
    """
    try:
        from rhosocial.activerecord.backend.dialect.protocols import (
            WindowFunctionSupport,
            AdvancedGroupingSupport,
            CTESupport,
            ReturningSupport,
        )

        from .utils import get_current_backend
        backend = get_current_backend()

        if backend is None:
            return

        dialect = backend.dialect
        unsupported_important_capabilities = []

        if not isinstance(dialect, WindowFunctionSupport) or not dialect.supports_window_functions():
            unsupported_important_capabilities.append("Window Functions")

        if not isinstance(dialect, AdvancedGroupingSupport):
            if not (hasattr(dialect, 'supports_cube') and dialect.supports_cube()):
                unsupported_important_capabilities.append("CUBE Grouping")
            if not (hasattr(dialect, 'supports_rollup') and dialect.supports_rollup()):
                unsupported_important_capabilities.append("ROLLUP Grouping")
        else:
            if hasattr(dialect, 'supports_cube') and not dialect.supports_cube():
                unsupported_important_capabilities.append("CUBE Grouping")
            if hasattr(dialect, 'supports_rollup') and not dialect.supports_rollup():
                unsupported_important_capabilities.append("ROLLUP Grouping")

        if not isinstance(dialect, CTESupport) or not dialect.supports_basic_cte():
            unsupported_important_capabilities.append("Common Table Expressions")

        if not isinstance(dialect, ReturningSupport) or not dialect.supports_returning_clause():
            unsupported_important_capabilities.append("RETURNING Clause")

        if unsupported_important_capabilities:
            warnings.warn(
                f"Current backend does not support important capabilities: "
                f"{', '.join(unsupported_important_capabilities)}. "
                f"Some tests will be automatically skipped.",
                UserWarning
            )
    except Exception as e:
        warnings.warn(f"Could not check capability support at session start: {e}", UserWarning)