# src/rhosocial/activerecord/testsuite/feature/query/conftest.py
"""L2 model fixtures for the query topic.

Each fixture names its model directly and configures it against the database
whose ``database_config`` the current directory's conftest defines.  Which
versioned model file supplies the sync class is decided here, so tests only see
fixture names.

A fixture group is one unit of work: tests count queries on one model's
backend and expect the relation queries of the rest to go through that same
connection, so the group shares one backend instance (``BackendGroup``).
"""

import importlib
import sys

import pytest

from rhosocial.activerecord.connection import AsyncBackendGroup, BackendGroup
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


# --- the order group -------------------------------------------------------

ORDER_MODELS = (User, Order, OrderItem)
ASYNC_ORDER_MODELS = (AsyncUser, AsyncOrder, AsyncOrderItem)


@pytest.fixture(name="order_fixtures")
def order_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_order",
        models=list(ORDER_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield ORDER_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_order_fixtures")
async def async_order_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_order",
        models=list(ASYNC_ORDER_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_ORDER_MODELS
    await group.get_backend().disconnect()


# --- the blog group --------------------------------------------------------

BLOG_MODELS = (User, Post, Comment)
ASYNC_BLOG_MODELS = (AsyncUser, AsyncPost, AsyncComment)


@pytest.fixture(name="blog_fixtures")
def blog_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_blog",
        models=list(BLOG_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield BLOG_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_blog_fixtures")
async def async_blog_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_blog",
        models=list(ASYNC_BLOG_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_BLOG_MODELS
    await group.get_backend().disconnect()


# --- the JSON user ---------------------------------------------------------


@pytest.fixture(name="json_user_fixture")
def json_user_fixture(database_config):
    scenario, config, _name = database_config
    JsonUser.configure(config, scenario.backend_class)
    yield JsonUser
    JsonUser.backend().disconnect()


@pytest.fixture(name="async_json_user_fixture")
async def async_json_user_fixture(database_config):
    scenario, config, _name = database_config
    await AsyncJsonUser.configure(config, scenario.async_backend_class)
    yield AsyncJsonUser
    await AsyncJsonUser.backend().disconnect()


# --- the tree group --------------------------------------------------------


@pytest.fixture(name="tree_fixtures")
def tree_fixtures(database_config):
    scenario, config, _name = database_config
    Node.configure(config, scenario.backend_class)
    yield (Node,)
    Node.backend().disconnect()


@pytest.fixture(name="async_tree_fixtures")
async def async_tree_fixtures(database_config):
    scenario, config, _name = database_config
    await AsyncNode.configure(config, scenario.async_backend_class)
    yield (AsyncNode,)
    await AsyncNode.backend().disconnect()


# --- everything the combined queries need ----------------------------------

COMBINED_MODELS = (User, Order, OrderItem, Post, Comment)
ASYNC_COMBINED_MODELS = (AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment)


@pytest.fixture(name="combined_fixtures")
def combined_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_combined",
        models=list(COMBINED_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield COMBINED_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_combined_fixtures")
async def async_combined_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_combined",
        models=list(ASYNC_COMBINED_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_COMBINED_MODELS
    await group.get_backend().disconnect()


# --- the extended order group ---------------------------------------------

EXTENDED_ORDER_MODELS = (ExtendedUser, ExtendedOrder, ExtendedOrderItem)
ASYNC_EXTENDED_ORDER_MODELS = (
    AsyncExtendedUser,
    AsyncExtendedOrder,
    AsyncExtendedOrderItem,
)


@pytest.fixture(name="extended_order_fixtures")
def extended_order_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_extended_order",
        models=list(EXTENDED_ORDER_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield EXTENDED_ORDER_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_extended_order_fixtures")
async def async_extended_order_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_extended_order",
        models=list(ASYNC_EXTENDED_ORDER_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_EXTENDED_ORDER_MODELS
    await group.get_backend().disconnect()


# --- full-text search ------------------------------------------------------


@pytest.fixture(name="annotated_query_fixtures")
def annotated_query_fixtures(database_config):
    scenario, config, _name = database_config
    SearchableItem.configure(config, scenario.backend_class)
    yield SearchableItem
    SearchableItem.backend().disconnect()


@pytest.fixture(name="async_annotated_query_fixtures")
async def async_annotated_query_fixtures(database_config):
    scenario, config, _name = database_config
    await AsyncSearchableItem.configure(config, scenario.async_backend_class)
    yield AsyncSearchableItem
    await AsyncSearchableItem.backend().disconnect()


# --- mapped column names ---------------------------------------------------

MAPPED_MODELS = (MappedUser, MappedPost, MappedComment)
ASYNC_MAPPED_MODELS = (AsyncMappedUser, AsyncMappedPost, AsyncMappedComment)


@pytest.fixture(name="mapped_models_fixtures")
def mapped_models_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_mapped",
        models=list(MAPPED_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield MAPPED_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_mapped_models_fixtures")
async def async_mapped_models_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_mapped",
        models=list(ASYNC_MAPPED_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_MAPPED_MODELS
    await group.get_backend().disconnect()


# --- the profile group -----------------------------------------------------

PROFILE_MODELS = (User, Profile)
ASYNC_PROFILE_MODELS = (AsyncUser, AsyncProfile)


@pytest.fixture(name="profile_fixtures")
def profile_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_profile",
        models=list(PROFILE_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield PROFILE_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_profile_fixtures")
async def async_profile_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_profile",
        models=list(ASYNC_PROFILE_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_PROFILE_MODELS
    await group.get_backend().disconnect()


# --- the basic composite-key order item ------------------------------------


@pytest.fixture(name="order_item_class")
def order_item_class(database_config):
    scenario, config, _name = database_config
    BasicOrderItem.configure(config, scenario.backend_class)
    yield BasicOrderItem
    BasicOrderItem.backend().disconnect()


@pytest.fixture(name="async_order_item_class")
async def async_order_item_class(database_config):
    scenario, config, _name = database_config
    await AsyncBasicOrderItem.configure(config, scenario.async_backend_class)
    yield AsyncBasicOrderItem
    await AsyncBasicOrderItem.backend().disconnect()
