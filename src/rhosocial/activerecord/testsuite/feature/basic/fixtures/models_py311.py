# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py311.py
"""Python 3.11+ fixture view: ``typing.Self`` and ``typing.LiteralString``.

Models live once in their group modules and are re-exported by ``models.py``;
``resolve()`` finds no real model of a given name here, so every other name
falls through to the 3.8 baseline.  This file only exposes a version-specific
probe: ``Self`` appears on a method return (never in a column), while
``LiteralString`` is used as a column annotation that must still behave as
``str``.
"""

from typing import LiteralString, Self

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 11)


class TypingProbe311:
    """Probe that ``Self`` and ``LiteralString`` are available at runtime."""

    @classmethod
    def table_name(cls) -> Self:
        return "typing_probe_311"

    id: int | None = None
    label: LiteralString = None
