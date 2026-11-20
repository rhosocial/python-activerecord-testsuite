# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py312.py
"""Python 3.12+ fixture view: ``typing.override`` (PEP 698).

Models live once in their group modules and are re-exported by ``models.py``;
``resolve()`` finds no real model of a given name here, so every other name
falls through to the 3.8 baseline.  This file only exposes a version-specific
probe: ``@override`` marks the overridden ``table_name()`` and is unavailable
on Python 3.11 and below.
"""

from typing import override

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 12)


class _TypingProbe312Base:
    """Tiny base so ``@override`` on the probe has something to override."""

    @classmethod
    def table_name(cls):
        return "typing_probe_312_base"


class TypingProbe312(_TypingProbe312Base):
    """Probe that ``typing.override`` is available."""

    @classmethod
    @override
    def table_name(cls):
        return "typing_probe_312"

    id: int | None = None
    label: str = None
