# src/rhosocial/activerecord/testsuite/feature/ddl/conftest.py
"""Pytest fixtures for the backend-independent DDLSource contract group."""

import pytest

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


@pytest.fixture
def bare_class():
    return BareItem


@pytest.fixture
def spec_order_class():
    return SpecOrder


@pytest.fixture
def capability_class():
    return CapabilityPost


@pytest.fixture
def spec_comment_class():
    return SpecComment


@pytest.fixture
def async_bare_class():
    return AsyncBareItem


@pytest.fixture
def async_spec_order_class():
    return AsyncSpecOrder


@pytest.fixture
def async_capability_class():
    return AsyncCapabilityPost


@pytest.fixture
def async_spec_comment_class():
    return AsyncSpecComment
