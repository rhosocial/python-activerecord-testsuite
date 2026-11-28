# src/rhosocial/activerecord/testsuite/feature/rules/backend/expression/test_registry.py
"""The registry and retired-API contracts every backend runs unchanged.

A backend bridges this module and supplies ``subject`` and ``registry`` in its
own conftest. Nothing here names a backend or decides which table is correct.
"""

from rhosocial.activerecord.testsuite.feature.rules.contracts.registry import *  # noqa: F401,F403,E501
from rhosocial.activerecord.testsuite.feature.rules.contracts.retired import *  # noqa: F401,F403,E501
from rhosocial.activerecord.testsuite.feature.rules.contracts.explicit import *  # noqa: F401,F403,E501
