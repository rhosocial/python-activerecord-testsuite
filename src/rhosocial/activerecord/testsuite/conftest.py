# src/rhosocial/activerecord/testsuite/conftest.py
"""
This file serves as the root pytest configuration for the entire testsuite package.
Its purpose is to define global configurations and hooks for pytest, such as
registering custom markers that can be used to categorize and filter tests.
"""
import pytest

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
