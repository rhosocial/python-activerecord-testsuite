# src/rhosocial/activerecord/testsuite/feature/rules/contracts/ownership.py
"""The naming rule, which presupposes an owner.

A subject that owns proprietary vocabulary writes its own name in front of every
node it declares. The prefix is what keeps that vocabulary distinguishable
wherever only a class name survives -- a kind string, a traceback, a serialized
payload -- and a node carrying the owner's name must not also be a core
expression name: one description with two owners is the same defect as two
names for one description.

This lives apart from :mod:`.naming` because the claim has a premise the other
claims do not: an owner must exist. The generic side has none -- it *is* the
vocabulary, so there is no name to claim and no second owner to collide with.
Rather than define the test there and skip it, the module is simply not imported
on that side: a rule that does not apply is not a rule that ran and found
nothing.

What this cannot see: the same limits as :mod:`.naming` -- a node defined
outside the subject's directories, a class built at run time, a base whose alias
the reader cannot resolve. And, by design, a generic-side name that merely looks
like some backend's: recognising it would require the knowledge the generic side
is defined not to have.
"""

from __future__ import annotations

from typing import List

from .naming import core_vocabulary, nodes
from .subject import ExpressionSubject


def naming_offenders(subject: ExpressionSubject) -> List[str]:
    """Unprefixed nodes, and nodes that reuse a core expression name.

    Requires ``subject.prefix``: a subject without one has no owner to name. The
    caller is a test module that only owners import, so this is a precondition
    rather than a branch.
    """
    if not subject.has_vocabulary_owner:
        raise AssertionError(
            f"{subject.label} has no vocabulary owner; the naming claim does not "
            "apply and this module should not be imported for it"
        )
    core_names = {name for _, name in core_vocabulary()}
    problems: List[str] = []
    for label, relative, name in nodes(subject):
        where = f"{label}/{relative.as_posix()}"
        if not name.lstrip("_").startswith(subject.prefix):
            problems.append(f"{where}: {name} does not start with {subject.prefix}")
        if name in core_names:
            problems.append(f"{where}: {name} reuses a core expression name")
    return problems


def test_expression_nodes_are_named_by_their_owner(subject: ExpressionSubject) -> None:
    """Every node carries the owner's name and never a core name.

    The two checks are one claim: a name must say who owns it. An unprefixed
    node claims nothing; a node named after a core class claims the wrong owner.
    """
    offenders = naming_offenders(subject)
    assert not offenders, (
        f"nodes whose name does not belong to {subject.label}:\n" + "\n".join(offenders)
    )
