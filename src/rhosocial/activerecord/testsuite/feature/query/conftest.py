# src/rhosocial/activerecord/testsuite/feature/query/conftest.py
"""Fixtures for the query topic.

Each fixture names its model directly; the testsuite environment configures it
against the directory's database.  Which versioned model file supplies the
class is decided here, so tests only see fixture names.
"""
import importlib
import sys

import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    AsyncOrderItem as AsyncBasicOrderItem,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    OrderItem as BasicOrderItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.annotated_adapter_models import (
    SearchableItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_annotated_adapter_models import (
    AsyncSearchableItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_blog_models import (
    AsyncComment,
    AsyncPost,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import (
    AsyncNode,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_extended_models import (
    AsyncExtendedOrder,
    AsyncExtendedOrderItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_extended_models import (
    AsyncUser as AsyncExtendedUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_json_models import (
    AsyncJsonUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncProfile,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node
from rhosocial.activerecord.testsuite.feature.query.fixtures.extended_models import (
    ExtendedOrder,
    ExtendedOrderItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.extended_models import (
    User as ExtendedUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import (
    AsyncMappedComment,
    AsyncMappedPost,
    AsyncMappedUser,
)

FIXTURES_PACKAGE = "rhosocial.activerecord.testsuite.feature.query.fixtures"

VERSION_MODULES = (("312", (3, 12)), ("311", (3, 11)), ("310", (3, 10)))


def resolve(name: str):
    """Return the newest versioned model class available, or the baseline one."""
    for suffix, required in VERSION_MODULES:
        if sys.version_info < required:
            continue
        module_path = f"{FIXTURES_PACKAGE}.models_py{suffix}"
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            continue
        candidate = getattr(module, name, None)
        if candidate is not None:
            return candidate
    return getattr(importlib.import_module(f"{FIXTURES_PACKAGE}.models"), name)


User = resolve("User")
Order = resolve("Order")
OrderItem = resolve("OrderItem")
Post = resolve("Post")
Comment = resolve("Comment")
Profile = resolve("Profile")
JsonUser = resolve("JsonUser")
MappedUser = resolve("MappedUser")
MappedPost = resolve("MappedPost")
MappedComment = resolve("MappedComment")


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


def _share_first_backend(models):
    """Let every model in a group use the first model's backend instance.

    A group is one unit of work: the tests count queries on one model's backend
    and expect the relation queries of the rest to go through that same
    connection.  The extra backends the environment configured are not used
    once their model points at the first one, so they are closed here.
    """
    first = models[0]
    for model in models[1:]:
        previous = getattr(model, "__backend__", None)
        model.__backend__ = first.__backend__
        model.__connection_config__ = first.__connection_config__
        model.__backend_class__ = first.__backend_class__
        if previous is not None and previous is not first.__backend__:
            previous.disconnect()


async def _share_first_backend_async(models):
    """Let every async model in a group share the first model's backend."""
    first = models[0]
    for model in models[1:]:
        previous = getattr(model, "__backend__", None)
        model.__backend__ = first.__backend__
        model.__connection_config__ = first.__connection_config__
        model.__backend_class__ = first.__backend_class__
        if previous is not None and previous is not first.__backend__:
            await previous.disconnect()


def _configure(environment, models):
    configured = tuple(environment.configure(model) for model in models)
    _share_first_backend(configured)
    return configured


async def _configure_async(environment, models):
    configured = tuple([await environment.configure_async(model) for model in models])
    await _share_first_backend_async(configured)
    return configured


def _disconnect_group(models) -> None:
    """Disconnect the group's backends once, however many models point at it."""
    seen = set()
    for model in models:
        backend = getattr(model, "__backend__", None)
        if backend is None or id(backend) in seen:
            continue
        seen.add(id(backend))
        backend.disconnect()


async def _disconnect_group_async(models) -> None:
    seen = set()
    for model in models:
        backend = getattr(model, "__backend__", None)
        if backend is None or id(backend) in seen:
            continue
        seen.add(id(backend))
        await backend.disconnect()


# --- the order group -------------------------------------------------------

ORDER_MODELS = (User, Order, OrderItem)
ASYNC_ORDER_MODELS = (AsyncUser, AsyncOrder, AsyncOrderItem)


@pytest.fixture(name="order_fixtures")
def order_fixtures(environment):
    models = _configure(environment, ORDER_MODELS)
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_order_fixtures")
async def async_order_fixtures(environment):
    models = await _configure_async(environment, ASYNC_ORDER_MODELS)
    yield models
    await _disconnect_group_async(models)


# --- the blog group --------------------------------------------------------

BLOG_MODELS = (User, Post, Comment)
ASYNC_BLOG_MODELS = (AsyncUser, AsyncPost, AsyncComment)


@pytest.fixture(name="blog_fixtures")
def blog_fixtures(environment):
    models = _configure(environment, BLOG_MODELS)
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_blog_fixtures")
async def async_blog_fixtures(environment):
    models = await _configure_async(environment, ASYNC_BLOG_MODELS)
    yield models
    await _disconnect_group_async(models)


# --- the JSON user ---------------------------------------------------------


@pytest.fixture(name="json_user_fixture")
def json_user_fixture(environment):
    model = environment.configure(JsonUser)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_json_user_fixture")
async def async_json_user_fixture(environment):
    model = await environment.configure_async(AsyncJsonUser)
    yield model
    await _disconnect_async(model)


# --- the tree group --------------------------------------------------------


@pytest.fixture(name="tree_fixtures")
def tree_fixtures(environment):
    models = _configure(environment, (Node,))
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_tree_fixtures")
async def async_tree_fixtures(environment):
    models = await _configure_async(environment, (AsyncNode,))
    yield models
    await _disconnect_group_async(models)


# --- everything the combined queries need ----------------------------------

COMBINED_MODELS = (User, Order, OrderItem, Post, Comment)
ASYNC_COMBINED_MODELS = (AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment)


@pytest.fixture(name="combined_fixtures")
def combined_fixtures(environment):
    models = _configure(environment, COMBINED_MODELS)
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_combined_fixtures")
async def async_combined_fixtures(environment):
    models = await _configure_async(environment, ASYNC_COMBINED_MODELS)
    yield models
    await _disconnect_group_async(models)


# --- the extended order group ---------------------------------------------

EXTENDED_ORDER_MODELS = (ExtendedUser, ExtendedOrder, ExtendedOrderItem)
ASYNC_EXTENDED_ORDER_MODELS = (
    AsyncExtendedUser,
    AsyncExtendedOrder,
    AsyncExtendedOrderItem,
)


@pytest.fixture(name="extended_order_fixtures")
def extended_order_fixtures(environment):
    models = _configure(environment, EXTENDED_ORDER_MODELS)
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_extended_order_fixtures")
async def async_extended_order_fixtures(environment):
    models = await _configure_async(environment, ASYNC_EXTENDED_ORDER_MODELS)
    yield models
    await _disconnect_group_async(models)


# --- full-text search ------------------------------------------------------


@pytest.fixture(name="annotated_query_fixtures")
def annotated_query_fixtures(environment):
    model = environment.configure(SearchableItem)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_annotated_query_fixtures")
async def async_annotated_query_fixtures(environment):
    model = await environment.configure_async(AsyncSearchableItem)
    yield model
    await _disconnect_async(model)


# --- mapped column names ---------------------------------------------------

MAPPED_MODELS = (MappedUser, MappedPost, MappedComment)
ASYNC_MAPPED_MODELS = (AsyncMappedUser, AsyncMappedPost, AsyncMappedComment)


@pytest.fixture(name="mapped_models_fixtures")
def mapped_models_fixtures(environment):
    models = _configure(environment, MAPPED_MODELS)
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_mapped_models_fixtures")
async def async_mapped_models_fixtures(environment):
    models = await _configure_async(environment, ASYNC_MAPPED_MODELS)
    yield models
    await _disconnect_group_async(models)


# --- the profile group -----------------------------------------------------

PROFILE_MODELS = (User, Profile)
ASYNC_PROFILE_MODELS = (AsyncUser, AsyncProfile)


@pytest.fixture(name="profile_fixtures")
def profile_fixtures(environment):
    models = _configure(environment, PROFILE_MODELS)
    yield models
    _disconnect_group(models)


@pytest.fixture(name="async_profile_fixtures")
async def async_profile_fixtures(environment):
    models = await _configure_async(environment, ASYNC_PROFILE_MODELS)
    yield models
    await _disconnect_group_async(models)


# --- the basic composite-key order item ------------------------------------


@pytest.fixture(name="order_item_class")
def order_item_class(environment):
    model = environment.configure(BasicOrderItem)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_order_item_class")
async def async_order_item_class(environment):
    model = await environment.configure_async(AsyncBasicOrderItem)
    yield model
    await _disconnect_async(model)
