# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models_py314.py
"""Python 3.14+ fixture view: PEP 649/749 lazy annotation evaluation.

Models live once in their group modules and are re-exported by ``models.py``;
this file only exposes the version-specific probe.  Unlike the earlier version
files this is a *semantic* boundary, not a syntax one: annotations are no longer
evaluated while the class body runs.  ``TypingProbe314`` therefore carries a
forward reference to a name defined only *after* the class -- legal here
because evaluation is deferred to ``__annotate__``, a ``NameError`` on 3.13 and
earlier.  ``resolve()`` does not reach this file on those interpreters.
"""

from .models import *  # noqa: F401,F403

__requires_python__ = (3, 14)


class TypingProbe314:
    """Probe that annotations are bound lazily through ``__annotate__``."""

    @classmethod
    def table_name(cls):
        return "typing_probe_314"

    id: int = None
    tags: list[str] = None
    # Bare forward reference, not a string: only PEP 649 can defer this far.
    peer: ProbePeer314 = None  # noqa: F405,F821


class ProbePeer314:
    """Declared after the probe so the lazy annotation has something to bind."""
