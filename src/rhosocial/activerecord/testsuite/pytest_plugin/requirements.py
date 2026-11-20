# src/rhosocial/activerecord/testsuite/pytest_plugin/requirements.py
"""Evaluate the dialect requirements a declaration states.

A declaration says what it needs the dialect to answer yes to. It does not
say, and must not say, how a backend provides it: the mechanism is the dialect's
own business. Both channels -- a fixture definition's declaration and a concrete
case's marker -- go through :func:`reason`, so the two cannot drift apart.

The evaluation is deliberately strict:

* a method the dialect does not implement is a *gap in the dialect*, not an
  "unsupported feature": it raises instead of answering ``False``, because a
  silent negative would skip a whole suite the moment a dialect loses a method;
* a method that raises, or answers with something that is not a boolean, is
  likewise an error rather than a negative answer;
* only a genuine "no" produces a skip, and the reason names the method and the
  owner that required it.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple, Union

import pytest


class MissingRequirementError(RuntimeError):
    """A dialect does not implement a method a declaration required.

    This is a dialect gap, not a negative answer: the caller named a method,
    so a dialect without it cannot be judged unsupported -- it has not answered
    the question at all.
    """


@dataclass(frozen=True)
class Requirement:
    """One requirement: a dialect method name and the answer it must give."""

    method: str
    must: bool = True
    """``True``: the method must answer yes. ``False``: it must answer no."""

    def describe(self) -> str:
        return "{} (must answer {})".format(self.method, "yes" if self.must else "no")

    def satisfied_by(self, answered: bool) -> bool:
        return answered is self.must


Entry = Union[str, Requirement, Tuple[str, bool]]


def requirement_of(entry: Entry) -> Requirement:
    """Normalise a declared entry into a :class:`Requirement`.

    A bare string means "this method must answer yes"; a ``(name, must)`` tuple
    carries the polarity when it is "no".
    """
    if isinstance(entry, Requirement):
        return entry
    if isinstance(entry, str):
        return Requirement(entry, True)
    if isinstance(entry, tuple) and len(entry) == 2:
        return Requirement(entry[0], bool(entry[1]))
    raise TypeError("not a requirement: {!r}".format(entry))


def requirement_list(entries: Iterable[Entry]) -> Tuple[Requirement, ...]:
    return tuple(requirement_of(entry) for entry in entries)


def answer(dialect, name: str) -> bool:
    """Ask the dialect one method, strictly.

    Raises:
        MissingRequirementError: the dialect has no such method, or it raised,
            or it answered with a non-boolean.
    """
    dialect_name = getattr(dialect, "name", type(dialect).__name__)
    method = getattr(dialect, name, None)
    if method is None or not callable(method):
        raise MissingRequirementError(
            "{}.{}() is not implemented: the dialect never declared this "
            "answer".format(dialect_name, name)
        )
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):  # pragma: no cover - builtins and C methods
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
            raise MissingRequirementError(
                "{}.{}() takes {}: a requirement must be answered without an "
                "argument. Name the zero-argument method instead, or drop it "
                "from the declaration".format(
                    dialect_name, name, ", ".join(required)
                )
            )
    try:
        answered = method()
    except Exception as error:  # noqa: BLE001 - reported as a dialect fault
        raise MissingRequirementError(
            "{}.{}() raised {}: {}".format(
                dialect_name, name, type(error).__name__, error
            )
        ) from error
    if not isinstance(answered, bool):
        raise MissingRequirementError(
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

    Every requirement must hold: this is a conjunction, so the first unmet one
    names the reason.

    Raises:
        MissingRequirementError: forwarded from :func:`answer`.
    """
    for entry in requirements:
        requirement = requirement_of(entry)
        answered = answer(dialect, requirement.method)
        if not requirement.satisfied_by(answered):
            dialect_name = getattr(dialect, "name", type(dialect).__name__)
            return "{} requires {} but {}.{}() answered {}".format(
                owner,
                requirement.describe(),
                dialect_name,
                requirement.method,
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
    "MissingRequirementError",
    "Requirement",
    "answer",
    "reason",
    "require",
    "requirement_list",
    "requirement_of",
]
