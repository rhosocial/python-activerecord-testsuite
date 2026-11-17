# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py310.py
"""Python 310+ fixture view: PEP 604 ``X | Y`` union syntax.

Models live once in their group modules and are re-exported by ``models.py``;
``resolve()`` walks here first, finds no model of a given name, and falls
through to the baseline. This file only exposes a version-specific probe.
"""

try:  # Python 3.8 baseline has no PEP 604 in annotations at runtime here
    from typing import Optional
except ImportError:  # pragma: no cover
    from typing_extensions import Optional

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 10)


class TypingProbe310:
    """A model whose annotation uses PEP 604 ``X | Y`` union syntax, proving the interpreter parses it."""

    @classmethod
    def table_name(cls):
        return "typing_probe_310"

    id: Optional[int] = None
    label: str
