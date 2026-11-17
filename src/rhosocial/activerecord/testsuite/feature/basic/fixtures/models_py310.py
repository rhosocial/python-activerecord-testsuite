# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py310.py
"""Python 3.10+ fixture view: PEP 604 ``X | Y`` union syntax.

Models live once in their group modules and are re-exported by ``models.py``;
``resolve()`` finds no real model of a given name here, so every other name
falls through to the 3.8 baseline.  This file only exposes a version-specific
probe that proves the interpreter accepts PEP 604 unions in annotations.
"""

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 10)


class TypingProbe310:
    """Probe that PEP 604 ``X | Y`` unions are valid runtime annotations."""

    @classmethod
    def table_name(cls):
        return "typing_probe_310"

    id: int | None = None
    label: str | None = None
