# src/rhosocial/activerecord/testsuite/feature/mixins/conftest.py
"""Fixtures for the mixins topic.

Each fixture names its model directly; the testsuite environment configures it
against the directory's database.  Which versioned model file supplies the
class is decided here, so tests only see fixture names.

The directory owns one database and one fixture group: every test prepares all
four tables, even when it only uses one of the models.
"""
import pytest

from .fixtures import resolve
from .fixtures import tables

TimestampedPost = resolve("TimestampedPost")
AsyncTimestampedPost = resolve("AsyncTimestampedPost")
VersionedProduct = resolve("VersionedProduct")
AsyncVersionedProduct = resolve("AsyncVersionedProduct")
Task = resolve("Task")
AsyncTask = resolve("AsyncTask")
CombinedArticle = resolve("CombinedArticle")
AsyncCombinedArticle = resolve("AsyncCombinedArticle")

GROUP_TABLES = (
    "timestamped_posts",
    "versioned_products",
    "tasks",
    "combined_articles",
)


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.MIXINS_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


@pytest.fixture(name="timestamped_post_model")
def timestamped_post_model(environment):
    model = environment.configure(TimestampedPost)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_timestamped_post_model")
async def async_timestamped_post_model(environment):
    model = await environment.configure_async(AsyncTimestampedPost)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="versioned_product_model")
def versioned_product_model(environment):
    model = environment.configure(VersionedProduct)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_versioned_product_model")
async def async_versioned_product_model(environment):
    model = await environment.configure_async(AsyncVersionedProduct)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="task_model")
def task_model(environment):
    model = environment.configure(Task)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_task_model")
async def async_task_model(environment):
    model = await environment.configure_async(AsyncTask)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="combined_article_model")
def combined_article_model(environment):
    model = environment.configure(CombinedArticle)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_combined_article_model")
async def async_combined_article_model(environment):
    model = await environment.configure_async(AsyncCombinedArticle)
    yield model
    await _disconnect_async(model)
