# src/rhosocial/activerecord/testsuite/conftest.py
"""
This file serves as the root pytest configuration for the entire testsuite package.
Its purpose is to define global configurations and hooks for pytest, such as
registering custom markers that can be used to categorize and filter tests.
"""
import pytest
import warnings

def pytest_configure(config):
    """
    A pytest hook that runs at the beginning of a test session to configure
    the test environment.
    """
    # Register custom markers to allow for selective test runs.
    # For example, `pytest -m feature` will run only the core feature tests.
    config.addinivalue_line("markers", "feature: Core feature tests (must be run by all backends)")
    config.addinivalue_line("markers", "realworld: Real-world scenario tests (optional)")
    config.addinivalue_line("markers", "benchmark: Performance benchmark tests (optional)")
    config.addinivalue_line("markers", "requires_capability: Mark tests that require specific database capabilities")

def pytest_collection_modifyitems(config, items):
    """
    Hook to automatically skip tests that require unsupported capabilities.
    
    This hook checks each test for the requires_capability marker and skips
    tests that require capabilities not supported by the current backend.
    """
    try:
        # Get current backend instance
        # This would typically come from a fixture or configuration
        from .utils import get_current_backend
        backend = get_current_backend()
        
        for item in items:
            # Check for capability requirements
            requires_capability_marker = item.get_closest_marker("requires_capability")
            if requires_capability_marker:
                required_capabilities = requires_capability_marker.args[0]
                
                # Skip test if capabilities are not supported
                from .feature.utils import skip_if_capability_unsupported
                try:
                    skip_if_capability_unsupported(backend, required_capabilities)
                except pytest.skip.Exception:
                    # Test should be skipped, let pytest handle it
                    pass
    except Exception as e:
        # If we can't determine capability support, continue normally
        warnings.warn(f"Could not check capability support: {e}", UserWarning)

def pytest_sessionstart(session):
    """
    Hook to generate capability support warnings at session start.
    
    This hook generates warnings about important unsupported capabilities
    to alert developers about backend limitations.
    """
    try:
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
