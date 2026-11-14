# src/rhosocial/activerecord/testsuite/core/capabilities.py
"""Capability-driven skipping.

A test states what it needs instead of every backend keeping its own skip list:

* ``@requires_protocol((ProtocolClass, method_name))`` -- the dialect must
  implement the protocol (and advertise the named ``supports_*`` method when
  one is given);
* ``@requires_functions("json_array_insert", ...)`` -- the dialect's
  ``supports_functions()`` table must report every listed function.

The probe uses the dialect the directory environment opened for the test, so
version-dependent probes run against an adapted dialect.  Nothing is guessed:
a marker that cannot be evaluated lets the test run.
"""
from __future__ import annotations

import importlib
from typing import List, Optional, Sequence

import pytest

SCENARIO_FIXTURE_NAME = "backend_scenario"

_DIALECTS = {}


def scenario_of(item):
    """Return the scenario the item runs, taken from its parametrization.

    The suite's own fixture is ``backend_scenario``, but a backend's local
    tests may parameterize on their own scenario fixture (the MariaDB collation
    tests use ``mariadb_scenario``, for example).  Any parameter whose value
    looks like a scenario -- it carries ``backend_class`` and a ``name`` -- is
    therefore accepted; those tests touch the same per-directory database as
    the suite tests and must resolve to the same scenario.
    """
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return None
    scenario = callspec.params.get(SCENARIO_FIXTURE_NAME)
    if scenario is not None and hasattr(scenario, "backend_class"):
        return scenario
    for value in callspec.params.values():
        if hasattr(value, "backend_class") and hasattr(value, "name"):
            return value
    return None


def dialect_for(scenario):
    """Return an adapted dialect for a scenario, without needing a directory.

    Used by fixture definitions that only render statements (the DDL topic)
    and therefore have no directory database of their own.  The probe opens
    the backend on a temporary database, adapts the dialect, then cleans up;
    if the server cannot be reached the unadapted dialect is still returned.
    """
    key = getattr(scenario, "name", None)
    if key in _DIALECTS:
        return _DIALECTS[key]

    probe = "test_dialect_probe"
    maintenance = getattr(scenario, "maintenance_database", None)
    candidates = [maintenance] if maintenance else []
    candidates.extend((probe, ""))
    dialect = opened = None
    for database in candidates:
        try:
            backend = scenario.backend_class(
                connection_config=scenario.make_config(database)
            )
            backend.connect()
            backend.introspect_and_adapt()
            dialect = backend.dialect
            opened = database
            backend.disconnect()
            break
        except Exception:  # noqa: BLE001 - try the next probe shape
            dialect = None
    if dialect is None:
        backend = scenario.backend_class(
            connection_config=scenario.make_config(probe)
        )
        dialect = backend.dialect
    else:
        if opened not in (maintenance, ""):
            try:
                scenario.reset_database(opened)
            except Exception:  # noqa: BLE001 - probing must not fail the run
                pass
    _DIALECTS[key] = dialect
    return dialect


def resolve_protocol(protocol_class_or_name):
    if not isinstance(protocol_class_or_name, str):
        return protocol_class_or_name
    module_path, _, class_name = protocol_class_or_name.rpartition(".")
    return getattr(importlib.import_module(module_path), class_name)


def protocol_reason(dialect, protocol_class, method_name) -> Optional[str]:
    protocol_class = resolve_protocol(protocol_class)
    if protocol_class is None:
        return None
    if not isinstance(dialect, protocol_class):
        return f"backend dialect does not implement {protocol_class.__name__}"
    if not method_name:
        return None
    method = getattr(dialect, method_name, None)
    if method is None:
        return f"backend dialect has no {method_name}()"
    if method_name.startswith("supports_") and callable(method):
        try:
            supported = method()
        except Exception:  # noqa: BLE001 - a probe that cannot answer
            return f"{method_name}() raised on this backend"
        if supported is not True:
            return f"backend dialect does not support {method_name[len('supports_'):]}"
    return None


def function_reason(dialect, required: Sequence[str]) -> Optional[str]:
    if not required:
        return None
    probe = getattr(dialect, "supports_functions", None)
    if probe is None:
        return "backend dialect has no supports_functions()"
    try:
        supported = probe()
    except Exception:  # noqa: BLE001
        return "supports_functions() raised on this backend"
    missing: List[str] = []
    for name in required:
        info = supported.get(name, False) if hasattr(supported, "get") else False
        expected = getattr(info, "supported", info)
        if expected is not True:
            missing.append(name)
    if missing:
        return f"backend dialect does not support functions: {', '.join(missing)}"
    return None


def skip_if_unsupported(item, scenario, dialect) -> None:
    """Skip an item whose dialect cannot satisfy its capability markers."""
    protocol_marker = item.get_closest_marker("requires_protocol")
    functions_marker = item.get_closest_marker("requires_functions")
    if protocol_marker is None and functions_marker is None:
        return
    if dialect is None:
        return

    reason = None
    if protocol_marker is not None:
        info = protocol_marker.args[0] if protocol_marker.args else (None, None)
        if isinstance(info, (tuple, list)) and len(info) == 2:
            protocol_class, method_name = info
        else:
            protocol_class, method_name = info, None
        reason = protocol_reason(dialect, protocol_class, method_name)
    if reason is None and functions_marker is not None:
        required = functions_marker.args[0] if functions_marker.args else ()
        if isinstance(required, str):
            required = (required,)
        reason = function_reason(dialect, required)

    if reason:
        name = getattr(scenario, "name", "?")
        pytest.skip(f"[{name}] {reason}")


__all__ = ["dialect_for", "scenario_of", "skip_if_unsupported"]
