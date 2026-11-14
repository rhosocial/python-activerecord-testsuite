# src/rhosocial/activerecord/testsuite/feature/events/conftest.py
"""Fixtures for the events topic.

Each fixture names its model directly; the testsuite environment configures it
against the directory's database.  Which versioned model file supplies the
class is decided here, so tests only see fixture names.

The directory owns one database and one fixture group: every test prepares both
event tables, even when it only uses one of the models.
"""
import pytest

from .fixtures import resolve
from .fixtures import tables

EventTestModel = resolve("EventTestModel")
AsyncEventTestModel = resolve("AsyncEventTestModel")
EventTrackingModel = resolve("EventTrackingModel")
AsyncEventTrackingModel = resolve("AsyncEventTrackingModel")

GROUP_TABLES = (
    "event_tests",
    "event_tracking_models",
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
        environment.execute(tables.EVENTS_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


@pytest.fixture(name="event_model")
def event_model(environment):
    model = environment.configure(EventTestModel)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_event_model")
async def async_event_model(environment):
    model = await environment.configure_async(AsyncEventTestModel)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="event_tracking_model")
def event_tracking_model(environment):
    model = environment.configure(EventTrackingModel)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_event_tracking_model")
async def async_event_tracking_model(environment):
    model = await environment.configure_async(AsyncEventTrackingModel)
    yield model
    await _disconnect_async(model)
