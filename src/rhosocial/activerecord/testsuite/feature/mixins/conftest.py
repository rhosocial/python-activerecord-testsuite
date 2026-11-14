# src/rhosocial/activerecord/testsuite/feature/mixins/conftest.py
"""L2 environment and model fixtures for the mixins topic.

- ``database``: one database per directory (session scope, emptied at start);
- ``schema``: the four mixin tables, dropped and recreated for every test
  (function scope), so each test starts from empty tables;
- ``database_config``: the scenario, its connection configuration, and the
  directory database name, which the model fixtures configure against.

The directory owns one fixture group: every test prepares all four tables,
even when it only uses one of the models.  Which versioned model file supplies
the class is decided here, so tests only see fixture names.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.mixins.fixtures.definitions import (
    CombinedArticleDefinition,
    TaskDefinition,
    TimestampedPostDefinition,
    VersionedProductDefinition,
)

from .fixtures import resolve

TimestampedPost = resolve("TimestampedPost")
AsyncTimestampedPost = resolve("AsyncTimestampedPost")
VersionedProduct = resolve("VersionedProduct")
AsyncVersionedProduct = resolve("AsyncVersionedProduct")
Task = resolve("Task")
AsyncTask = resolve("AsyncTask")
CombinedArticle = resolve("CombinedArticle")
AsyncCombinedArticle = resolve("AsyncCombinedArticle")

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    TimestampedPostDefinition,
    VersionedProductDefinition,
    TaskDefinition,
    CombinedArticleDefinition,
)


def _database_name() -> str:
    """Database name from this conftest's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the directory database name."""
    name = _database_name()
    return backend_scenario, backend_scenario.make_config(name), name


@pytest.fixture(scope="session")
def database(database_config):
    """The directory's database, prepared once and left for later files."""
    scenario, config, name = database_config
    scenario.reset_database(name)
    backend = scenario.backend_class(connection_config=config)
    backend.connect()
    backend.introspect_and_adapt()
    yield backend
    backend.disconnect()


@pytest.fixture(scope="function", autouse=True)
def schema(database):
    """Drop and recreate the tables this directory uses, before every test."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


@pytest.fixture(name="timestamped_post_model")
def timestamped_post_model(database_config):
    scenario, config, _name = database_config
    TimestampedPost.configure(config, scenario.backend_class)
    yield TimestampedPost
    TimestampedPost.backend().disconnect()


@pytest.fixture(name="async_timestamped_post_model")
async def async_timestamped_post_model(database_config):
    scenario, config, _name = database_config
    await AsyncTimestampedPost.configure(config, scenario.async_backend_class)
    yield AsyncTimestampedPost
    await AsyncTimestampedPost.backend().disconnect()


@pytest.fixture(name="versioned_product_model")
def versioned_product_model(database_config):
    scenario, config, _name = database_config
    VersionedProduct.configure(config, scenario.backend_class)
    yield VersionedProduct
    VersionedProduct.backend().disconnect()


@pytest.fixture(name="async_versioned_product_model")
async def async_versioned_product_model(database_config):
    scenario, config, _name = database_config
    await AsyncVersionedProduct.configure(config, scenario.async_backend_class)
    yield AsyncVersionedProduct
    await AsyncVersionedProduct.backend().disconnect()


@pytest.fixture(name="task_model")
def task_model(database_config):
    scenario, config, _name = database_config
    Task.configure(config, scenario.backend_class)
    yield Task
    Task.backend().disconnect()


@pytest.fixture(name="async_task_model")
async def async_task_model(database_config):
    scenario, config, _name = database_config
    await AsyncTask.configure(config, scenario.async_backend_class)
    yield AsyncTask
    await AsyncTask.backend().disconnect()


@pytest.fixture(name="combined_article_model")
def combined_article_model(database_config):
    scenario, config, _name = database_config
    CombinedArticle.configure(config, scenario.backend_class)
    yield CombinedArticle
    CombinedArticle.backend().disconnect()


@pytest.fixture(name="async_combined_article_model")
async def async_combined_article_model(database_config):
    scenario, config, _name = database_config
    await AsyncCombinedArticle.configure(config, scenario.async_backend_class)
    yield AsyncCombinedArticle
    await AsyncCombinedArticle.backend().disconnect()
