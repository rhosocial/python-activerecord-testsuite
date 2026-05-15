# src/rhosocial/activerecord/testsuite/utils/__init__.py
"""
Testsuite utility functions.

This package provides utility functions for the testsuite:
- Protocol checking decorators for marking test requirements
- Runtime protocol validation functions
- Convenience decorators for common protocol requirements
- Fixture selection utilities
"""

from .common import (
    # Backend access
    get_current_backend,
    get_backend_from_model,

    # Protocol and function checking
    skip_test_if_protocol_unsupported,
    skip_test_if_functions_unsupported,

    # Decorators
    requires_protocol,
    requires_functions,

    # Convenience decorators
    requires_window_functions,
    requires_advanced_grouping,
    requires_cube,
    requires_rollup,
    requires_grouping_sets,
    requires_cte,
    requires_recursive_cte,
    requires_json_operations,
    requires_inner_join,
    requires_left_join,
    requires_cross_join,
    requires_natural_join,
    requires_right_join,
    requires_full_join,
    requires_lateral_joins,
    requires_upsert,
    requires_array_operations,
    requires_returning_clause,
    requires_set_operations,
)

from .fixture_selector import select_fixture

__all__ = [
    # Backend access
    'get_current_backend',
    'get_backend_from_model',

    # Protocol and function checking
    'skip_test_if_protocol_unsupported',
    'skip_test_if_functions_unsupported',

    # Decorators
    'requires_protocol',
    'requires_functions',

    # Convenience decorators
    'requires_window_functions',
    'requires_advanced_grouping',
    'requires_cube',
    'requires_rollup',
    'requires_grouping_sets',
    'requires_cte',
    'requires_recursive_cte',
    'requires_json_operations',
    'requires_inner_join',
    'requires_left_join',
    'requires_cross_join',
    'requires_natural_join',
    'requires_right_join',
    'requires_full_join',
    'requires_lateral_joins',
    'requires_upsert',
    'requires_array_operations',
    'requires_returning_clause',
    'requires_set_operations',

    # Fixture selection
    'select_fixture',
]
