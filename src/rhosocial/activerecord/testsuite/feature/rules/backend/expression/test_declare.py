# src/rhosocial/activerecord/testsuite/feature/rules/backend/expression/test_declare.py
"""The expression-to-formatter binding every backend must satisfy.

The assertions live in ``contracts.expression`` and are imported unchanged: a
backend bridges this module and declares its own ``subject``. What is checked is
that every node resolves to exactly one ``format_*``, that the name is spelled
as a formatter name, and that no name is declared twice inside the subject.
"""

from rhosocial.activerecord.testsuite.feature.rules.contracts.expression import *  # noqa: F401,F403,E501
