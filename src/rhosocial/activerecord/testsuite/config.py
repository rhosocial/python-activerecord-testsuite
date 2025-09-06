# python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/config.py
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

from rhosocial.activerecord.backend import ConnectionConfig
from rhosocial.activerecord.backend.impl.sqlite import SQLiteBackend, SQLiteConnectionConfig

# Define the base path for the test suite package
TEST_SUITE_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = TEST_SUITE_ROOT.parent.parent.parent.parent

# Backend driver mapping
BACKEND_DRIVERS = {
    "sqlite": SQLiteBackend,
    # Add other backends here, e.g.:
    # "mysql": MySQLBackend,
}

# Backend-specific connection config mapping
CONNECTION_CONFIGS = {
    "sqlite": SQLiteConnectionConfig,
    # Add other backends here, e.g.:
    # "mysql": MySQLConnectionConfig,
}

# Statically define configurations for all supported Python versions
BUILTIN_SQLITE_CONFIGS = {
    "3.8": {
        "sqlite_py38_mem": { "driver": "sqlite", "database": "file:memdb_py38?mode=memory&cache=shared", "uri": True },
        "sqlite_py38_file": { "driver": "sqlite", "database": "test_db_py38.sqlite", "delete_on_close": True }
    },
    "3.9": {
        "sqlite_py39_mem": { "driver": "sqlite", "database": "file:memdb_py39?mode=memory&cache=shared", "uri": True },
        "sqlite_py39_file": { "driver": "sqlite", "database": "test_db_py39.sqlite", "delete_on_close": True }
    },
    "3.10": {
        "sqlite_py310_mem": { "driver": "sqlite", "database": "file:memdb_py310?mode=memory&cache=shared", "uri": True },
        "sqlite_py310_file": { "driver": "sqlite", "database": "test_db_py310.sqlite", "delete_on_close": True }
    },
    "3.11": {
        "sqlite_py311_mem": { "driver": "sqlite", "database": "file:memdb_py311?mode=memory&cache=shared", "uri": True },
        "sqlite_py311_file": { "driver": "sqlite", "database": "test_db_py311.sqlite", "delete_on_close": True }
    },
    "3.12": {
        "sqlite_py312_mem": { "driver": "sqlite", "database": "file:memdb_py312?mode=memory&cache=shared", "uri": True },
        "sqlite_py312_file": { "driver": "sqlite", "database": "test_db_py312.sqlite", "delete_on_close": True }
    },
    "3.13": {
        "sqlite_py313_mem": { "driver": "sqlite", "database": "file:memdb_py313?mode=memory&cache=shared", "uri": True },
        "sqlite_py313_file": { "driver": "sqlite", "database": "test_db_py313.sqlite", "delete_on_close": True }
    },
    "3.14": {
        "sqlite_py314_mem": { "driver": "sqlite", "database": "file:memdb_py314?mode=memory&cache=shared", "uri": True },
        "sqlite_py314_file": { "driver": "sqlite", "database": "test_db_py314.sqlite", "delete_on_close": True }
    }
}

def get_target_python_version() -> str:
    """
    Determines the target Python version for testing.
    Checks PYTEST_TARGET_VERSION env var first, then falls back to current version.
    """
    target_version = os.environ.get("PYTEST_TARGET_VERSION")
    if target_version:
        return target_version
    
    py_version = sys.version_info
    return f"{py_version.major}.{py_version.minor}"

def load_backend_configs(config_path: Path = None) -> List[Dict[str, Any]]:
    """
    Load backend configurations.
    It loads the built-in SQLite configurations for the target Python version,
    and then loads any additional backend configurations from the user-provided YAML file.
    """
    parsed_configs = []
    
    # Get target Python version and load its built-in SQLite configs
    target_version_str = get_target_python_version()
    builtin_configs = BUILTIN_SQLITE_CONFIGS.get(target_version_str, {})
    
    for config_name, config_details in builtin_configs.items():
        backend_name = config_details.get("driver")
        parsed_configs.append({
            "backend_name": backend_name,
            "config_name": config_name,
            "driver": BACKEND_DRIVERS[backend_name],
            "config_class": CONNECTION_CONFIGS.get(backend_name, ConnectionConfig),
            "config_params": config_details
        })

    # Load user-provided configs from YAML for other backends
    if config_path is None:
        config_path = PROJECT_ROOT / "backends.yml"

    if config_path.exists():
        with open(config_path, 'r') as f:
            user_configs_by_backend = yaml.safe_load(f)
        
        if user_configs_by_backend:
            for backend_name, backend_configs in user_configs_by_backend.items():
                # Skip sqlite as it's handled by the built-in function
                if backend_name == 'sqlite':
                    continue
                
                if backend_name not in BACKEND_DRIVERS:
                    print(f"Warning: Backend '{backend_name}' not supported. Skipping.")
                    continue

                for config_name, config_details in backend_configs.items():
                    parsed_configs.append({
                        "backend_name": backend_name,
                        "config_name": config_name,
                        "driver": BACKEND_DRIVERS[backend_name],
                        "config_class": CONNECTION_CONFIGS.get(backend_name, ConnectionConfig),
                        "config_params": config_details
                    })

    return parsed_configs
