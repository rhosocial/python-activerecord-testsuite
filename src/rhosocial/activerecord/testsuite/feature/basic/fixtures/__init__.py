# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/__init__.py
"""Basic feature test fixtures.

``models.py`` is the Python 3.8 baseline.  The versioned files only add a
single syntax/semantics probe that exists on that interpreter; every other
name falls back to the baseline.  The newest file the running interpreter
supports wins.  Which class a fixture delivers is decided here, not by the
test.
"""

import importlib
import sys

# Newest first; 3.13 and 3.15 intentionally have no file of their own.
VERSION_MODULES = (
    ("314", (3, 14)),
    ("312", (3, 12)),
    ("311", (3, 11)),
    ("310", (3, 10)),
    ("39", (3, 9)),
)


def resolve(name: str):
    """Return the newest versioned model class available, or the baseline one."""
    package = __name__
    for suffix, required in VERSION_MODULES:
        if sys.version_info < required:
            continue
        module_path = f"{package}.models_py{suffix}"
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            continue
        candidate = getattr(module, name, None)
        if candidate is not None:
            return candidate
    return getattr(importlib.import_module(f"{package}.models"), name)
