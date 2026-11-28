# src/rhosocial/activerecord/testsuite/feature/rules/diagnose_layout.py
"""Read-only diagnostic for the expression layout *form* rule.

Run from any directory with the ``rhosocial.activerecord.backend`` namespace
path installed::

    python -m rhosocial.activerecord.testsuite.feature.rules.diagnose_layout

For every installed ``impl/<name>/expression`` package this prints the backend
name and its top-level sub-namespace names, then the union and intersection
across all backends. It is not a test: it imports no pytest, makes no assertions
and changes nothing. It exists so the pending design decision can be discussed
against what the installed trees actually contain.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Iterator, Tuple

from .contracts.layout import CANONICAL_NAMESPACES, expression_namespaces
from .contracts.subject import ExpressionSubject, Root

_BACKEND = "rhosocial.activerecord.backend"


def _installed_expression_packages() -> Iterator[Tuple[str, object]]:
    """Every installed ``impl/<name>/expression`` package, discovered by path."""
    backend = importlib.import_module(_BACKEND)
    names = set()
    for base in vars(backend).get("__path__", ()):
        impl = Path(base).resolve() / "impl"
        if not impl.is_dir():
            continue
        for entry in impl.iterdir():
            if (
                entry.is_dir()
                and not entry.name.startswith("_")
                and (entry / "expression").exists()
            ):
                names.add(entry.name)

    for name in sorted(names):
        module_name = f"{_BACKEND}.impl.{name}.expression"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # a broken optional backend must not stop the report
            print(f"{name}: cannot import {module_name}: {exc}", file=sys.stderr)
            continue
        yield name, module


def _subject_for(name: str, module: object) -> ExpressionSubject:
    """A minimal subject that points at the imported expression package."""
    paths = [Path(candidate).resolve() for candidate in vars(module).get("__path__", ())]
    if not paths:
        source = vars(module).get("__file__")
        if source:
            paths = [Path(source).resolve().parent]
    roots = tuple(Root(name, path, vars(module).get("__name__", name)) for path in paths)
    return ExpressionSubject(label=name, roots=roots)


def _package_location(module: object) -> str:
    """Where the expression package was loaded from."""
    paths = [str(Path(candidate).resolve()) for candidate in vars(module).get("__path__", ())]
    if paths:
        return ", ".join(paths)
    source = vars(module).get("__file__")
    return str(Path(source).resolve()) if source else "(unknown)"


def main() -> None:
    """Print the installed expression layouts and their union/intersection."""
    observed = {}
    print("Installed expression layouts (top-level sub-namespaces):")
    for name, module in _installed_expression_packages():
        namespaces = expression_namespaces(_subject_for(name, module))
        observed[name] = namespaces
        print(f"{name}: {', '.join(sorted(namespaces)) or '(none)'}")
        print(f"  loaded from: {_package_location(module)}")

    union = set().union(*observed.values()) if observed else set()
    intersection = set.intersection(*observed.values()) if observed else set()
    print(f"\nbackends observed: {len(observed)}")
    print(f"union:        {', '.join(sorted(union)) or '(none)'}")
    print(f"intersection: {', '.join(sorted(intersection)) or '(none)'}")
    if CANONICAL_NAMESPACES:
        print(f"canonical:    {', '.join(sorted(CANONICAL_NAMESPACES))}")
    else:
        print("canonical:    (not decided yet; diagnostic only, no rule is enforced)")


if __name__ == "__main__":
    main()
