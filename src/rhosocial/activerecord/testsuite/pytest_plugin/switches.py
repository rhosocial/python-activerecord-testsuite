# src/rhosocial/activerecord/testsuite/pytest_plugin/switches.py
"""Evaluate the dialect support switches a declaration requires.

Both channels -- a fixture definition's declaration and a concrete case's
marker -- go through :func:`reason`, so the two cannot drift apart.

The evaluation is deliberately strict:

* a switch the dialect does not implement is a *gap in the dialect*, not an
  "unsupported feature": it raises instead of answering ``False``, because a
  silent negative would skip a whole suite the moment a dialect loses a
  method;
* a probe that raises, or answers with something that is not a boolean, is
  likewise an error rather than a negative answer;
* only a genuine "no" produces a skip, and the reason names the switch and
  the owner that asked for it.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple, Union

import pytest


class MissingSwitchError(RuntimeError):
    """A dialect does not implement a switch that was declared.

    This is a dialect gap, not a negative capability answer: the caller
    declared a switch by name, so a dialect without that method cannot be
    judged unsupported -- it has not answered the question at all.
    """


@dataclass(frozen=True)
class Requirement:
    """One switch requirement, with the polarity it must hold in."""

    switch: str
    must: bool = True
    """``True``: the switch must answer yes. ``False``: it must answer no."""

    def describe(self) -> str:
        return "{} {}".format(self.switch, "(must be on)" if self.must else "(must be off)")

    def satisfied_by(self, answered: bool) -> bool:
        return answered is self.must


Entry = Union[str, Requirement, Tuple[str, bool]]


def requirement_of(entry: Entry) -> Requirement:
    """Normalise a declared entry into a :class:`Requirement`.

    A bare string means "this switch must answer yes"; a ``(name, must)``
    tuple carries the polarity when it is "off".
    """
    if isinstance(entry, Requirement):
        return entry
    if isinstance(entry, str):
        return Requirement(entry, True)
    if isinstance(entry, tuple) and len(entry) == 2:
        return Requirement(entry[0], bool(entry[1]))
    raise TypeError("not a switch requirement: {!r}".format(entry))


def requirement_list(entries: Iterable[Entry]) -> Tuple[Requirement, ...]:
    return tuple(requirement_of(entry) for entry in entries)


def answer(dialect, name: str) -> bool:
    """Ask the dialect one switch, strictly.

    Raises:
        MissingSwitchError: the dialect has no such switch, or the probe
            raised, or it answered with a non-boolean.
    """
    dialect_name = getattr(dialect, "name", type(dialect).__name__)
    probe = getattr(dialect, name, None)
    if probe is None or not callable(probe):
        raise MissingSwitchError(
            "{}.{}() is not implemented: the dialect never declared this "
            "switch".format(dialect_name, name)
        )
    try:
        signature = inspect.signature(probe)
    except (TypeError, ValueError):  # pragma: no cover - builtins and C probes
        signature = None
    if signature is not None:
        required = [
            parameter.name
            for parameter in signature.parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        if required:
            raise MissingSwitchError(
                "{}.{}() takes {}: a declared switch must answer without an "
                "argument. Name the zero-argument capability instead, or drop "
                "the switch from the declaration".format(
                    dialect_name, name, ", ".join(required)
                )
            )
    try:
        answered = probe()
    except Exception as error:  # noqa: BLE001 - reported as a dialect fault
        raise MissingSwitchError(
            "{}.{}() raised {}: {}".format(
                dialect_name, name, type(error).__name__, error
            )
        ) from error
    if not isinstance(answered, bool):
        raise MissingSwitchError(
            "{}.{}() answered {!r} instead of a boolean".format(
                dialect_name, name, answered
            )
        )
    return answered


def reason(
    dialect,
    requirements: Sequence[Entry],
    owner: str,
) -> Optional[str]:
    """Return why the requirements are not met, or ``None`` when they are.

    Every requirement must hold: this is a conjunction, so the first unmet
    one names the reason.

    Raises:
        MissingSwitchError: forwarded from :func:`answer`.
    """
    for entry in requirements:
        requirement = requirement_of(entry)
        answered = answer(dialect, requirement.switch)
        if not requirement.satisfied_by(answered):
            dialect_name = getattr(dialect, "name", type(dialect).__name__)
            return "{} requires {} but {}.{}() answered {}".format(
                owner,
                requirement.describe(),
                dialect_name,
                requirement.switch,
                answered,
            )
    return None


def require(
    dialect,
    requirements: Sequence[Entry],
    owner: str,
) -> None:
    """Skip the current test unless every requirement holds."""
    why = reason(dialect, requirements, owner)
    if why is not None:
        pytest.skip(why)


__all__ = [
    "Entry",
    "MissingSwitchError",
    "Requirement",
    "answer",
    "reason",
    "require",
    "requirement_list",
    "requirement_of",
]
