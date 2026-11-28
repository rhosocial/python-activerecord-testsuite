# src/rhosocial/activerecord/testsuite/feature/rules/contracts/subject.py
"""What a rule examines: one namespace, described once.

A subject answers four questions, and nothing else is needed to run a namespace
rule against it:

* **which trees belong to it** -- the directories whose classes it owns, each
  with the label a report should use and the dotted module prefix the tree
  contributes to;
* **where its expression namespace is** -- the first-level directory name inside
  those trees that holds its expression nodes;
* **whether it carries a name prefix** -- the side of the split that owns
  proprietary vocabulary writes its own name in front of its classes; the
  generic side has no owner to name, so it carries none;
* **which package root must stay open** -- the namespace directory that no
  ``__init__.py`` may close.

The module prefix is not decoration: a class name is not unique across a tree.
``Procedure`` is an expression object in one module and a plain base class in
another, and a rule that keyed on the bare name would treat a subclass of the
second as a node of the first. Resolution is therefore ``(module, name)``, and
each tree has to say what module it contributes to.

Fields carry the differences, which is what makes one implementation serve both
sides. ``prefix is None`` does not mean "no value supplied": it is the generic
side's actual state, and the naming rule reads it as "this subject has no
proprietary vocabulary, so the prefix claim does not apply".

What this module does **not** contain is knowledge of any concrete backend. A
backend is described by whoever tests it, in that backend's own tree; nothing
shared here may name one, count them, or assume they are installed.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, NamedTuple, Optional, Tuple

CORE_BASE = "BaseExpression"
CORE_EXPRESSION_MODULE = "rhosocial.activerecord.backend.expression"

#: Directories whose contents are documentation, not vocabulary. A demo names a
#: class the way its reader would, and no distribution assembles or registers
#: anything from it. ``examples/`` is out of scope for now; those scripts are
#: planned to move to ``docs/``, so both names are listed and the exclusion
#: survives the move unchanged.
DEMONSTRATION_DIRS: FrozenSet[str] = frozenset({"examples", "docs"})


class Root(NamedTuple):
    """One tree a subject owns, and the module it contributes to."""

    label: str
    path: Path
    module: str


@dataclass(frozen=True)
class ExpressionSubject:
    """One namespace of expression nodes, as a rule sees it."""

    #: How reports name this subject. The generic layer uses ``"core"``; a
    #: backend uses its own name, chosen by that backend's own test tree.
    label: str

    #: The trees whose classes belong to this subject.
    roots: Tuple[Root, ...]

    #: First-level directory names that are this subject's expression
    #: namespace. A tuple rather than a single name so a subject that later
    #: splits its vocabulary can say so without the rule changing.
    expression_dirs: Tuple[str, ...] = ("expression",)

    #: The owner's name, or ``None`` for the side that owns no vocabulary.
    prefix: Optional[str] = None

    #: Top-level directory names inside a root that do not belong to this
    #: subject. The generic side excludes ``impl``: that is the extension point
    #: where concrete implementations are contributed, not its own vocabulary.
    excluded_dirs: Tuple[str, ...] = ()

    #: The namespace directory that must not be closed by an ``__init__.py``.
    open_package_root: Optional[Path] = None

    #: The implementation package this subject owns, as a dotted module.
    #: ``None`` for the generic side, which owns none: every import into an
    #: implementation package is then foreign, and the one-way rule needs no
    #: list of backends to state it.
    impl_module_prefix: Optional[str] = None

    #: Directories whose classes are demonstrations rather than vocabulary.
    demonstration_dirs: FrozenSet[str] = field(default=DEMONSTRATION_DIRS)

    @property
    def has_vocabulary_owner(self) -> bool:
        """Whether this subject owns proprietary vocabulary and must name it."""
        return self.prefix is not None


def expression_root() -> Path:
    """The directory of core's generic expression package."""
    package = importlib.import_module(CORE_EXPRESSION_MODULE)
    for candidate in vars(package).get("__path__", ()):
        path = Path(candidate).resolve()
        if path.is_dir():
            return path
    raise AssertionError("the installed core expression package exposes no directory")


def core_expression_root() -> Root:
    """Core's expression package as a root with its module prefix."""
    return Root("core-expression", expression_root(), CORE_EXPRESSION_MODULE)
