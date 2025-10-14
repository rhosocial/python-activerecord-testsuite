# src/rhosocial/activerecord/testsuite/feature/test_features.py
"""Test the feature support mechanism itself."""

import pytest
from rhosocial.activerecord.backend.capabilities import (
    DatabaseCapabilities,
    CapabilityCategory,
    WindowFunctionCapability,
    AdvancedGroupingCapability
)
from .utils import requires_capability

class TestCapabilitySupport:
    """Test the DatabaseCapabilities class."""

    def test_capability_support_declaration(self):
        """Test declaring capability support."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function(WindowFunctionCapability.ROW_NUMBER)

        assert capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)
        assert not capabilities.supports_window_function(WindowFunctionCapability.RANK)

    def test_capability_support_multiple(self):
        """Test declaring multiple capability supports."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function([
            WindowFunctionCapability.ROW_NUMBER,
            WindowFunctionCapability.RANK
        ])

        assert capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)
        assert capabilities.supports_window_function(WindowFunctionCapability.RANK)
        assert not capabilities.supports_window_function(WindowFunctionCapability.LAG)

    def test_category_support(self):
        """Test category support."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function(WindowFunctionCapability.ROW_NUMBER)

        assert capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)
        assert not capabilities.supports_category(CapabilityCategory.ADVANCED_GROUPING)

@requires_capability(WindowFunctionCapability.ROW_NUMBER)
def test_requires_capability_decorator():
    """Test the requires_capability decorator.

    This test would be automatically skipped if WINDOW_FUNCTIONS is not supported
    by the current backend.
    """
    # This test just verifies the decorator can be applied
    assert True

@requires_capability([AdvancedGroupingCapability.CUBE, AdvancedGroupingCapability.ROLLUP])
def test_requires_multiple_capabilities():
    """Test the requires_capability decorator with multiple capabilities.

    This test would be automatically skipped if either CUBE or ROLLUP is not supported
    by the current backend.
    """
    # This test just verifies the decorator can be applied
    assert True
