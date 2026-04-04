# src/rhosocial/activerecord/testsuite/core/protocols.py
"""
Protocol definitions for WorkerPool testing.

This module defines the protocols that backends must implement to support
WorkerPool testing with serializable connection parameters.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class WorkerTestProtocol(Protocol):
    """
    Protocol for backends that support WorkerPool testing.

    Backends implementing this protocol can provide serializable connection
    parameters that allow Worker processes to connect to the same database
    used in the main test process.

    This is optional - backends that don't support WorkerPool testing
    simply don't implement this protocol.
    """

    def get_worker_connection_params(self, scenario_name: str, fixture_type: str = None) -> dict:
        """
        Return serializable connection parameters for Worker processes.

        This method provides all information needed to recreate the database
        connection in a Worker process.

        Args:
            scenario_name: The test scenario name
            fixture_type: Optional fixture type hint (e.g., 'order', 'user')
                         for providers that manage multiple fixture types

        Returns:
            dict: A dictionary containing:
                - backend_module: Module path for the backend class
                - backend_class_name: Name of the backend class
                - config_class_module: Module path for the config class
                - config_class_name: Name of the config class
                - config_kwargs: Dictionary of config constructor arguments
                - schema_sql: Optional SQL to create required tables
        """
        ...

    def get_worker_schema_sql(self, scenario_name: str, table_name: str) -> str:
        """
        Return the SQL statement to create a specific table.

        Args:
            scenario_name: The test scenario name
            table_name: Name of the table to create

        Returns:
            CREATE TABLE SQL statement
        """
        ...
