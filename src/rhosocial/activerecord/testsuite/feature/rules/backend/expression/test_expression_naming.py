# src/rhosocial/activerecord/testsuite/feature/rules/backend/test_expression_naming.py
"""The namespace rules every backend must satisfy.

Two modules, imported unchanged: ``contracts.naming`` holds the claims that hold
for any subject -- placement, and the openness of the package root --
``contracts.ownership`` holds the naming claim, which presupposes an owner and is
therefore imported only here, where an owner exists.

A backend bridges this module, declares its own ``subject`` in its conftest,
and runs the same claims. Nothing here names a backend, and nothing here decides
which subject is correct.
"""

from rhosocial.activerecord.testsuite.feature.rules.contracts.naming import *  # noqa: F401,F403,E501
from rhosocial.activerecord.testsuite.feature.rules.contracts.ownership import *  # noqa: F401,F403,E501
