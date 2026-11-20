# src/rhosocial/activerecord/testsuite/feature/mixins/fixtures/__init__.py
"""Mixins feature test fixtures.

``models.py`` is the Python 3.8 baseline.  ``models_py310.py`` and later only
add syntax that exists on those interpreters; the newest file the running
interpreter supports wins.  Which class a fixture delivers is decided here,
not by the test.
"""
import importlib
import sys

VERSION_MODULES = (("312", (3, 12)), ("311", (3, 11)), ("310", (3, 10)))


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
