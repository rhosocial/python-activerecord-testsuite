# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py39.py
"""Python 3.9+ fixture view: PEP 585 built-in generic annotations.

Models live once in their group modules and are re-exported by ``models.py``.
``resolve()`` finds no real model of a given name here, so every name other
than this file's probe falls through to the 3.8 baseline.  The probe exists to
prove the interpreter accepts ``list[str]`` / ``dict[str, int]`` as runtime
annotations -- the one syntax that raises ``TypeError`` outright on 3.8.
"""

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 9)


class TypingProbe39:
    """Probe that PEP 585 built-in generics are valid runtime annotations."""

    @classmethod
    def table_name(cls):
        return "typing_probe_39"

    id: int = None
    tags: list[str] = None
    scores: dict[str, int] = None
