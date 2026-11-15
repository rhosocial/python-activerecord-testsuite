# src/rhosocial/activerecord/testsuite/pytest_plugin/hooks.py
"""The pytest behaviour the suite adds, as plain functions.

``testsuite/plugin.py`` is the module pytest loads and it calls these, so the
mechanism can be read without the registration noise.

Three moments:

* **collection** -- a declared parallel directory is pinned to one worker per
  scenario, and the text a test carries (its purpose, what a pass or a failure
  means) is attached to the item so it reaches the report;
* **call** -- the switches a case declares are evaluated against the dialect
  the directory's environment opened, and an unmet one skips the case by name;
  this is ``call`` and not ``setup`` because the dialect exists only once the
  environment fixture has run;
* **report** -- a failure prints what it means, because ``-v`` does not show
  docstrings and a bare assertion message says nothing about the system.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

import pytest

from .declarations import DirectoryDeclaration, declaration_for
from .switches import MissingSwitchError, reason

REQUIRES_SWITCH = "requires_switch"
ABSENT_SWITCH = "absent_switch"
REQUIRES_PROTOCOL = "requires_protocol"
SCENARIO_FIXTURE = "backend_scenario"

#: Fixtures through which an already adapted dialect is reachable at call time.
#: ``environment`` is the legacy fixture kept for directories not yet migrated.
_DIALECT_FIXTURES = ("ddl_dialect", "database", "environment")

_SECTION = re.compile(r"^(purpose|passes|fails):\s*(.*)$", re.IGNORECASE)


def parse_docstring(text: Optional[str]) -> Tuple[str, Dict[str, str]]:
    """Split a docstring into its summary line and ``passes:``/``fails:`` text.

    Parsing never fails a test: the text is presentation, so anything
    unrecognised is simply left out.
    """
    if not text:
        return "", {}
    summary = ""
    sections: Dict[str, str] = {}
    current = None
    for line in text.strip().splitlines():
        stripped = line.strip()
        match = _SECTION.match(stripped)
        if match:
            current = match.group(1).lower()
            sections[current] = match.group(2).strip()
            continue
        if not stripped:
            continue
        if current is not None:
            sections[current] = (sections[current] + " " + stripped).strip()
        elif not summary:
            summary = stripped
    if summary:
        sections.setdefault("purpose", summary)
    return summary, sections


def scenario_name(item) -> str:
    """The scenario this item runs, from its parametrization."""
    callspec = getattr(item, "callspec", None)
    scenario = getattr(callspec, "params", {}).get(SCENARIO_FIXTURE)
    return getattr(scenario, "name", None) or "default"


def dialect_of(item):
    """The dialect the directory's environment opened, or ``None``."""
    funcargs = getattr(item, "funcargs", None) or {}
    for name in _DIALECT_FIXTURES:
        holder = funcargs.get(name)
        dialect = getattr(holder, "dialect", None) if holder is not None else None
        if dialect is not None:
            return dialect
    return None


def _protocol_reason(dialect, marker, owner: str) -> Optional[str]:
    """Why a ``requires_protocol`` marker is unmet, or ``None``."""
    info = marker.args[0] if marker.args else (None, None)
    if isinstance(info, (tuple, list)) and len(info) == 2:
        protocol_class, switch = info
    else:
        protocol_class, switch = info, None
    if protocol_class is None:
        return None
    if isinstance(protocol_class, str):
        import importlib

        module_path, _, class_name = protocol_class.rpartition(".")
        protocol_class = getattr(importlib.import_module(module_path), class_name)
    if not isinstance(dialect, protocol_class):
        return "{} needs {} but the dialect does not implement it".format(
            owner, protocol_class.__name__
        )
    if not switch:
        return None
    return reason(dialect, (switch,), owner)


def declared_requirements(item) -> List[Tuple[object, str]]:
    """Every switch requirement the item carries, in declaration order.

    ``iter_markers`` is used on purpose: ``get_closest_marker`` would return
    only the nearest declaration and silently drop the class or module one.
    """
    found: List[Tuple[object, str]] = []
    for marker in item.iter_markers(name=REQUIRES_SWITCH):
        for entry in marker.args:
            found.append((entry, REQUIRES_SWITCH))
    for marker in item.iter_markers(name=ABSENT_SWITCH):
        for entry in marker.args:
            found.append(((entry, False) if isinstance(entry, str) else entry, ABSENT_SWITCH))
    for marker in item.iter_markers(name=REQUIRES_PROTOCOL):
        found.append((marker, REQUIRES_PROTOCOL))
    return found


def evaluate(item) -> None:
    """Skip the item when a switch it declares does not hold.

    A dialect that never implemented a declared switch is a gap, not an
    "unsupported" answer, so it fails the item with a one-line message
    instead of a negative skip or a traceback.
    """
    entries = declared_requirements(item)
    if not entries:
        return
    try:
        dialect = dialect_of(item)
        if dialect is None:
            raise MissingSwitchError(
                "the directory opened no dialect, so the switch a case declares "
                "cannot be answered; a case marker belongs on a "
                "database-backed test"
            )
        for entry, marker_name in entries:
            owner = "{} ({})".format(getattr(item, "name", item.nodeid), marker_name)
            why = (
                _protocol_reason(dialect, entry, owner)
                if marker_name == REQUIRES_PROTOCOL
                else reason(dialect, (entry,), owner)
            )
            if why is not None:
                pytest.skip("[{}] {}".format(scenario_name(item), why))
    except MissingSwitchError as error:
        pytest.fail("{}: {}".format(item.nodeid, error), pytrace=False)

def attach_text(item, declaration: Optional[DirectoryDeclaration]) -> None:
    """Attach the text a test carries to its item, for the report.

    Specificity decides: the case's own text wins over its class, which wins
    over its file, which wins over the directory.  A broader layer only fills
    keys the narrower one left empty.
    """
    texts: Dict[str, str] = {}
    for source in (
        getattr(item, "obj", None),
        getattr(item, "cls", None),
        getattr(item, "module", None),
    ):
        _, sections = parse_docstring(getattr(source, "__doc__", None))
        for key, value in sections.items():
            if not value:
                continue
            name = "purpose" if key == "purpose" else key + "_means"
            texts.setdefault(name, value)
    if declaration is not None:
        for key, value in (
            ("directory_purpose", declaration.purpose),
            ("directory_passes_means", declaration.passes_means),
            ("directory_fails_means", declaration.fails_means),
        ):
            if value:
                texts.setdefault(key, value)
    if texts:
        item.user_properties.extend(texts.items())


def collection_modifyitems(config, items) -> None:
    """Pin declared parallel directories, and attach each item's text."""
    for item in items:
        path = getattr(item, "path", None)
        if path is None:
            continue
        declaration = declaration_for(config.pluginmanager, path)
        if declaration is not None and declaration.parallel:
            item.add_marker(
                pytest.mark.xdist_group(
                    "testsuite::{}::{}".format(
                        os.path.dirname(str(path)), scenario_name(item)
                    )
                )
            )
        attach_text(item, declaration)


def runtest_call(item) -> None:
    evaluate(item)


def logreport(report) -> None:
    """Say what a failure means, where the failure is reported."""
    if not report.failed or report.when != "call":
        return
    props = dict(getattr(report, "user_properties", ()) or ())
    consequence = (
        props.get("fails_means")
        or props.get("class_fails_means")
        or props.get("directory_fails_means")
    )
    if not consequence:
        return
    purpose = (
        props.get("purpose")
        or props.get("class_purpose")
        or props.get("directory_purpose")
    )
    body = consequence if not purpose else "{}\nunder test: {}".format(consequence, purpose)
    report.sections.append(("test implication", body))


__all__ = [
    "ABSENT_SWITCH",
    "REQUIRES_PROTOCOL",
    "REQUIRES_SWITCH",
    "attach_text",
    "collection_modifyitems",
    "declared_requirements",
    "dialect_of",
    "evaluate",
    "logreport",
    "parse_docstring",
    "runtest_call",
    "scenario_name",
]
