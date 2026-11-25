# tests/test_no_regex_in_src.py
"""``src`` uses plain string operations, never regular expressions.

The suite is itself test code, and a test that normalises generated SQL with a
regex becomes a second parser of the thing under test: it can accept SQL no
backend would emit, and its breadth is invisible where the assertion is read.
Plain string operations keep the assertion about the dialect. This guard makes
the rule mechanical instead of a review habit.

The scan is over this repository's ``src`` tree only; test modules may still
hold a regex where the regex *is* the expectation (an asserted SQL form).
"""

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"

#: The module whose import is banned, as the root of any dotted path.
_REGEX_MODULE = "re"

#: An attribute read off the module. Checked on text, not only on the AST,
#: because an alias (``import re as _re``) is easy to miss in review while the
#: attribute use is what actually binds a pattern.
_REGEX_ATTRIBUTE = re.compile(r"(?<![\w.])re\.[A-Za-z_]")


def _src_files():
    """Every Python module this repository ships."""
    return sorted(SRC.rglob("*.py"))


def _regex_imports(tree):
    """Yield ``(lineno, statement)`` for each import of the regex module."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == _REGEX_MODULE:
                    yield node.lineno, f"import {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] == _REGEX_MODULE:
                yield node.lineno, f"from {module} import ..."


def test_src_tree_is_scanable():
    """The other scans are only meaningful if they actually see modules."""
    assert _src_files(), f"no Python modules found under {SRC}"


def test_src_imports_no_regex_module():
    """No ``src`` module imports ``re``, under any spelling."""
    offenders = []
    for path in _src_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno, statement in _regex_imports(tree):
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {statement}")
    assert not offenders, "the regex module is imported in src:\n" + "\n".join(offenders)


def test_src_uses_no_regex_attributes():
    """No ``src`` line reads an attribute off the regex module."""
    offenders = []
    for path in _src_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if _REGEX_ATTRIBUTE.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, "regex use in src:\n" + "\n".join(offenders)
