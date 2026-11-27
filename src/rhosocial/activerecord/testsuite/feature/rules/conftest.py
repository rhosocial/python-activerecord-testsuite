# src/rhosocial/activerecord/testsuite/feature/rules/conftest.py
"""Scope declaration for the semantic-rule modules.

Every assertion here reads an expression, an AST or a type name; none opens a
connection. A dialect, where one is needed, is taken from core's ``dummy``
implementation, so a backend that installs the testsuite can run these modules
without a configured provider. These tests are neither sync nor async: the
objects they inspect have no sync/async halves, so no ``*_async.py`` twin is
called for.

The mechanical audits that used to live under this topic (constants, shared
defaults, catalogues) remain in core's own ``feature/rules`` tree and are not
duplicated here. The protocol-requirement decorators are covered by
``feature/contracts/test_features.py`` and are likewise not repeated.
"""

from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    parallel=False,
    uses_database=False,
    purpose="Executable assertions of the formal expression/dialect semantics",
    passes_means="the implementation answers the formal description's section",
    fails_means="the implementation contradicts the formal description",
)
