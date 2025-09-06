# src/rhosocial/activerecord/testsuite/utils/helpers.py
import logging
from pathlib import Path

# Setup logger
logger = logging.getLogger('testsuite_helpers')


def get_schema_path(test_node, schema_dir) -> Path:
    """Determine the schema file path based on the test file's location."""
    schema_name = Path(test_node.fspath).parent.name
    schema_file = Path(schema_dir) / f"{schema_name}.sql"
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found for test: {test_node.name}. Expected at: {schema_file}")
        
    return schema_file

def setup_database(config, test_node):
    """Connect to the database and set up the schema."""
    config_params = config["config_params"].copy()
    ConnectionConfigClass = config["config_class"]
    backend_class = config["driver"]

    if "driver" in config_params:
        del config_params["driver"]
    
    schema_dir = config_params.pop("schema_dir", None)
    if not schema_dir:
        raise ValueError("schema_dir not defined in backend configuration")

    # Create connection config and backend instance
    connection_config = ConnectionConfigClass(**config_params)
    backend = backend_class(connection_config=connection_config)
    
    try:
        # Load and execute schema
        schema_path = get_schema_path(test_node, schema_dir)
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Split and execute statements
        for statement in schema_sql.split(';'):
            if statement.strip():
                backend.execute(statement)
        
        logger.info(f"Successfully set up schema from {schema_path} for backend {config['backend_name']}")
        return backend, connection_config
    except Exception as e:
        logger.error(f"Failed to set up database for {config['backend_name']}: {e}")
        if backend:
            backend.disconnect()
        raise

def teardown_database(backend, backend_name):
    """Drop all tables and disconnect from the database."""
    if not backend:
        return
        
    try:
        with backend.transaction():
            backend.execute("DROP TABLE IF EXISTS users;")
            backend.execute("DROP TABLE IF EXISTS type_cases;")
            backend.execute("DROP TABLE IF EXISTS validated_field_users;")
            backend.execute("DROP TABLE IF EXISTS type_tests;")
            backend.execute("DROP TABLE IF EXISTS validated_users;")
            logger.info(f"Dropped all tables for backend {backend_name}")
    except Exception as e:
        logger.error(f"Failed to drop tables for backend {backend_name}: {e}")
    finally:
        backend.disconnect()
        logger.info(f"Successfully tore down database for backend {backend_name}")