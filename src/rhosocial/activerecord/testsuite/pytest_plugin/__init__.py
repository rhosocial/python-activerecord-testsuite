# src/rhosocial/activerecord/testsuite/pytest_plugin/__init__.py
"""The suite's pytest mechanism: declarations, switch evaluation, reporting.

This package replaces the previous ``testsuite/core`` layer, whose capability
module was deleted as a negative example.  Nothing here names a backend, a
server version, or a mechanism: a declaration names dialect switches, and the
dialect is the only thing that answers them.
"""
from .declarations import DirectoryDeclaration, declaration_for
from .switches import (
    MissingSwitchError,
    Requirement,
    answer,
    reason,
    require,
    requirement_list,
    requirement_of,
)

__all__ = [
    "DirectoryDeclaration",
    "MissingSwitchError",
    "Requirement",
    "answer",
    "declaration_for",
    "reason",
    "require",
    "requirement_list",
    "requirement_of",
]
