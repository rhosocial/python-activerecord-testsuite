# src/rhosocial/activerecord/testsuite/feature/rules/contracts/imports.py
"""Implementation packages are entered by nobody but their owner.

The dependency between the two sides of the split runs one way: an implementation
imports the generic layer, never the reverse, and implementations do not import
each other. Each side is expressed as the same claim with a different subject:

* the generic layer owns no implementation, so **every** import reaching into an
  implementation package is foreign;
* an implementation owns exactly one package, so an import reaching into a
  different one is foreign, and an import of its own is the ordinary inside
  reference.

That is one rule, parameterised by ``impl_module_prefix``: ``None`` for the
generic subject (nothing is yours), the subject's own module for a backend.

A dependency can be written four ways, and all four are read: an absolute
import, a relative one resolved through its module, an imported member whose
dotted name names the package, and a dynamic import -- ``import_module`` or
``__import__`` -- whose literal argument names it. Types of prose that mention a
package are not imports: a docstring example or a CLI ``prog`` string executes
nothing, and the scan reads the AST rather than the text.

What this cannot see: a module reached by ``getattr`` on a computed name, and a
dynamic import whose argument is built at run time. Those are named rather than
assumed absent.
"""

from __future__ import annotations

import ast
from typing import List, Tuple

from .naming import Tree, module_of, source_files
from .subject import ExpressionSubject

IMPL_ROOT = "rhosocial.activerecord.backend.impl."
IMPL_HEADS = ("rhosocial.activerecord.backend.impl.", "impl.")


def _is_impl(module: str) -> bool:
    """Whether a dotted module names an implementation package."""
    if module.startswith(IMPL_ROOT):
        return True
    head = module.lstrip(".")
    return head == "impl" or head.startswith("impl.")


def _foreign(subject: ExpressionSubject, module: str) -> bool:
    """Whether this import leaves the subject's own implementation package."""
    if not _is_impl(module):
        return False
    own = subject.impl_module_prefix
    if own is None:
        return True
    head = module.lstrip(".")
    if head == "impl" or head.startswith("impl."):
        # A relative import names only the tail; whether it points at the
        # subject's own package depends on where it was written, so the caller
        # resolves the absolute form before asking.
        return True
    return not module.startswith(own + ".") and module != own


def _dynamic_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def imported_modules(subject: ExpressionSubject) -> List[Tuple[str, int, str]]:
    """Every import inside the subject's trees, as ``(file, line, module)``."""
    skip = set(subject.excluded_dirs) | set(subject.demonstration_dirs)
    found: List[Tuple[str, int, str]] = []
    for root in subject.roots:
        for path in source_files(root.path):
            relative = path.relative_to(root.path)
            if skip & set(relative.parts):
                continue
            module = module_of(root, relative)
            package = module if relative.name == "__init__.py" else module.rsplit(".", 1)[0]
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        found.append((relative.as_posix(), node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    source = Tree._source_module(package, node.level, node.module)
                    if source:
                        found.append((relative.as_posix(), node.lineno, source))
                    for alias in node.names:
                        if "." in alias.name:
                            found.append((relative.as_posix(), node.lineno, alias.name))
                elif isinstance(node, ast.Call):
                    if _dynamic_name(node) not in {"import_module", "__import__"}:
                        continue
                    if not node.args:
                        continue
                    argument = node.args[0]
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        found.append((relative.as_posix(), node.lineno, argument.value))
    return found


def foreign_imports(subject: ExpressionSubject) -> List[str]:
    """Imports that reach into an implementation package not this subject's."""
    return [
        f"{path}:{lineno}: imports {module}"
        for path, lineno, module in imported_modules(subject)
        if _foreign(subject, module)
    ]


def test_no_module_imports_a_foreign_implementation(subject: ExpressionSubject) -> None:
    """The dependency runs one way, and implementations do not reach each other."""
    offenders = foreign_imports(subject)
    assert not offenders, (
        f"imports of an implementation package that {subject.label} does not own:\n"
        + "\n".join(offenders)
    )
