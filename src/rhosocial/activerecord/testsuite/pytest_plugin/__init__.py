# src/rhosocial/activerecord/testsuite/pytest_plugin/__init__.py
"""The suite's pytest mechanism: declarations, requirements, reporting.

This package replaces the previous ``testsuite/core`` layer, whose capability
module was deleted as a negative example.  Nothing here names a backend, a
server version, or a mechanism: a declaration states what it requires the
dialect to answer yes to, and the dialect is the only thing that answers.
"""
from .declarations import Declaration, declaration_for
from .requirements import (
    MissingRequirementError,
    Requirement,
    answer,
    reason,
    require,
    requirement_list,
    requirement_of,
)

__all__ = [
    "Declaration",
    "MissingRequirementError",
    "Requirement",
    "answer",
    "declaration_for",
    "reason",
    "require",
    "requirement_list",
    "requirement_of",
]
