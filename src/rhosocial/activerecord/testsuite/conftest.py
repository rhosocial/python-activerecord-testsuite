# src/rhosocial/activerecord/testsuite/conftest.py
import pytest
from .config import load_backend_configs
from .utils.helpers import setup_database, teardown_database, get_schema_path
import logging

logger = logging.getLogger(__name__)

# Load all backend configurations to parameterize tests
def pytest_generate_tests(metafunc):
    if "database" in metafunc.fixturenames:
        backend_configs = load_backend_configs()
        ids = [f"{c['backend_name']}-{c['config_name']}" for c in backend_configs]
        metafunc.parametrize("database", backend_configs, ids=ids, scope="function", indirect=True)

@pytest.fixture(scope="function")
def database(request):
    """Main fixture to set up and tear down a database session for each test."""
    config = request.param
    
    # Setup database: connect and create schema
    backend, connection_config = setup_database(config, request.node)
    
    yield backend, connection_config
    
    # Teardown database: drop schema and disconnect
    teardown_database(backend, config['backend_name'])

@pytest.fixture
def user_class(database):
    """Provides a User model class configured for the current db_session."""
    from .feature.basic.fixtures.models import User
    backend, config = database
    User.configure(config=config, backend_class=type(backend))
    return User

@pytest.fixture
def type_case_class(database):
    """Provides a TypeCase model class configured for the current db_session."""
    from .feature.basic.fixtures.models import TypeCase
    backend, config = database
    TypeCase.configure(config=config, backend_class=type(backend))
    return TypeCase

@pytest.fixture
def validated_user_class(database):
    """Provides a ValidatedFieldUser model class configured for the current db_session."""
    from .feature.basic.fixtures.models import ValidatedFieldUser
    backend, config = database
    ValidatedFieldUser.configure(config=config, backend_class=type(backend))
    return ValidatedFieldUser

@pytest.fixture
def type_test_model_class(database):
    """Provides a TypeTestModel model class configured for the current db_session."""
    from .feature.basic.fixtures.models import TypeTestModel
    backend, config = database
    TypeTestModel.configure(config=config, backend_class=type(backend))
    return TypeTestModel

@pytest.fixture
def validated_user(database):
    """Provides a ValidatedUser model class configured for the current db_session."""
    from .feature.basic.fixtures.models import ValidatedUser
    backend, config = database
    ValidatedUser.configure(config=config, backend_class=type(backend))
    return ValidatedUser
