# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py311.py
"""Python 311+ fixture view: ``typing.Self`` and ``LiteralString``.

Models live once in their group modules and are re-exported by ``models.py``;
``resolve()`` walks here first, finds no model of a given name, and falls
through to the baseline. This file only exposes a version-specific probe.
"""

try:  # Python 3.8 baseline has no PEP 604 in annotations at runtime here
    from typing import Optional
except ImportError:  # pragma: no cover
    from typing_extensions import Optional

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 11)


class TypingProbe311:
    """A model whose annotation uses ``typing.Self`` and ``LiteralString``, proving the interpreter parses it."""

    @classmethod
    def table_name(cls):
        return "typing_probe_311"

    id: Optional[int] = None
    label: str
