# src/rhosocial/activerecord/testsuite/feature/worker/conftest.py
"""
Fixture definitions for WorkerPool testing.

Core principles:
- WorkerPool instance is a fixture, not created in test logic
- Environment is prepared by Provider, ready when test executes
- Schema-agnostic, schema is managed by backend Provider

Limitations:
- SQLite :memory: scenario does not support WorkerPool testing,
  as in-memory databases cannot be shared across processes
"""
import os
import importlib
import pytest
from typing import Dict, Any

from rhosocial.activerecord.worker import WorkerPool

# Reuse scenario definitions from basic feature
from rhosocial.activerecord.testsuite.feature.basic.conftest import (
    SCENARIO_PARAMS
)


def _get_worker_tasks_module_path() -> str:
    """
    Get the worker_tasks module path.

    Reads from environment variable TESTSUITE_WORKER_TASKS_MODULE,
    defaults to 'providers.worker_tasks'.

    Returns:
        Module path string
    """
    return os.environ.get(
        'TESTSUITE_WORKER_TASKS_MODULE',
        'providers.worker_tasks'
    )


@pytest.fixture(scope="function")
def worker_pool():
    """
    WorkerPool fixture.

    Each test uses an independent WorkerPool instance,
    which is automatically shut down after the test.
    """
    pool = WorkerPool(n_workers=4, check_interval=0.1)
    yield pool
    pool.shutdown()


@pytest.fixture(scope="function")
def worker_tasks():
    """
    Worker task functions fixture.

    Dynamically imports the task functions module provided by the backend.

    Returns:
        Module object containing functions like create_user_task, read_user_task, etc.
    """
    module_path = _get_worker_tasks_module_path()
    return importlib.import_module(module_path)


def _is_memory_database(config) -> bool:
    """
    Detect if the database is an in-memory database.

    SQLite :memory: databases cannot be shared across processes,
    making them unsuitable for WorkerPool testing.
    """
    # Check for SQLite memory database
    if hasattr(config, 'database'):
        if config.database == ':memory:':
            return True
        # Check for URI format memory database
        if config.database.startswith('file:') and 'memory' in config.database:
            return True
    return False


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def worker_connection_params(request, user_class) -> Dict[str, Any]:
    """
    Extract serializable connection parameters from configured model.

    The environment is already prepared by the user_class fixture,
    this just extracts connection information for Worker use.

    Args:
        request: pytest request object
        user_class: Configured model class (environment ready)

    Returns:
        dict: Serializable connection parameters for task functions
            - backend_module: module where backend class is defined
            - backend_class_name: backend class name
            - config_module: module where config class is defined
            - config_class_name: config class name
            - config_dict: serializable config parameters

    Raises:
        pytest.skip: If using in-memory database, skip the test
    """
    backend = user_class.backend()
    config = backend.config

    # Detect in-memory database and skip unsupported scenario
    if _is_memory_database(config):
        pytest.skip("WorkerPool tests do not support :memory: database (cross-process isolation)")

    # Get backend class information
    backend_class = type(backend)
    backend_module = backend_class.__module__
    backend_class_name = backend_class.__name__

    # Get config class information
    config_class = type(config)
    config_module = config_class.__module__
    config_class_name = config_class.__name__

    # Extract serializable parameters from config
    config_dict = config.to_dict()

    return {
        'backend_module': backend_module,
        'backend_class_name': backend_class_name,
        'config_module': config_module,
        'config_class_name': config_class_name,
        'config_dict': config_dict,
    }
