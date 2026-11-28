# src/rhosocial/activerecord/testsuite/feature/rules/contracts/explicit.py
"""No dynamic attribute access, regex, or string-boundary dispatch in owners.

An expression name, a kind, or a capability is an identity. Looking it up with
``getattr``/``hasattr``, a regular expression, or a prefix/suffix test makes the
identity depend on a spelling rather than a declaration: a rename silently
changes behaviour, and a typo can resolve to something the owner never meant to
publish. Names must come from explicit classes, members, tables, or sets.

The audit is static (``ast``) and follows the owner's expression and
registration files, not its driver/connection machinery.
"""

from __future__ import annotations

import ast
from typing import List

from .retired import _audited_files
from .subject import ExpressionSubject

_DYNAMIC_CALLS = {"getattr", "setattr", "hasattr"}
_STRING_BOUNDARIES = {"startswith", "endswith"}


def _offenders(subject: ExpressionSubject) -> List[str]:
    found = []
    for path in _audited_files(subject):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "re" for alias in node.names):
                    found.append(f"{path.as_posix()}:{node.lineno}: 're' import")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "re":
                    found.append(f"{path.as_posix()}:{node.lineno}: 're' import")
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in _DYNAMIC_CALLS:
                found.append(f"{path.as_posix()}:{node.lineno}: {node.func.id}()")
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in _STRING_BOUNDARIES:
                    found.append(f"{path.as_posix()}:{node.lineno}: .{node.func.attr}()")
                if (
                    node.func.attr in {"compile", "match", "search", "sub", "fullmatch"}
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "re"
                ):
                    found.append(f"{path.as_posix()}:{node.lineno}: re.{node.func.attr}()")
    return found


def test_no_dynamic_identity_lookups(subject: ExpressionSubject) -> None:
    """Identities are declared, never discovered by spelling."""
    offenders = _offenders(subject)
    assert not offenders, "dynamic identity lookup in the owner's tree:\n" + "\n".join(
        offenders
    )
