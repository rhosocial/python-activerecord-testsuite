# src/rhosocial/activerecord/testsuite/feature/ddl/conftest.py
"""Fixtures for the backend-independent DDLSource contract group.

These tests render statements and inspect declarations; they never create
tables.  The dialect comes straight from the scenario the test runs, so no
directory database is needed.
"""
import pytest

from rhosocial.activerecord.testsuite.core.capabilities import dialect_for

from .fixtures.models import (
    AsyncBareItem,
    AsyncCapabilityPost,
    AsyncSpecComment,
    AsyncSpecOrder,
    BareItem,
    CapabilityPost,
    SpecComment,
    SpecOrder,
)


@pytest.fixture(name="ddl_dialect")
def ddl_dialect(backend_scenario):
    """Provide a backend dialect instance for statement rendering."""
    return dialect_for(backend_scenario)


@pytest.fixture(name="async_ddl_dialect")
def async_ddl_dialect(backend_scenario):
    """Provide the same dialect for statements derived from async models."""
    return dialect_for(backend_scenario)


@pytest.fixture(name="bare_class")
def bare_class():
    return BareItem


@pytest.fixture(name="spec_order_class")
def spec_order_class():
    return SpecOrder


@pytest.fixture(name="capability_class")
def capability_class():
    return CapabilityPost


@pytest.fixture(name="spec_comment_class")
def spec_comment_class():
    return SpecComment


@pytest.fixture(name="async_bare_class")
def async_bare_class():
    return AsyncBareItem


@pytest.fixture(name="async_spec_order_class")
def async_spec_order_class():
    return AsyncSpecOrder


@pytest.fixture(name="async_capability_class")
def async_capability_class():
    return AsyncCapabilityPost


@pytest.fixture(name="async_spec_comment_class")
def async_spec_comment_class():
    return AsyncSpecComment
