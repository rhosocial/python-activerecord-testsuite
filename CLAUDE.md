# Project Overview: rhosocial-activerecord-testsuite

## Project Identification

- **Repository Name**: python-activerecord-testsuite
- **Python Package Name**: rhosocial-activerecord-testsuite
- **Version**: 1.0.0.dev* (tracks core package for API compatibility)

## Project Purpose

This project is a standardized test suite for the `rhosocial-activerecord` Python package. It provides contracts for features, real-world scenarios, and benchmarks to validate backend implementations.

## Dependencies

- **Core Package**: `rhosocial-activerecord>=1.0.0,<2.0.0`
- **Testing Framework**: pytest, pytest-asyncio
- **Python Version**: 3.8+ (same as core package)

## Path Assumptions

- `python-activerecord/` and `python-activerecord-testsuite/` are sibling
  directories. Backend projects (`python-activerecord-mysql`,
  `python-activerecord-postgres`, etc.) are also siblings and import this
  testsuite via 1-to-1 mirror trees under their own `tests/`.

## Rules (the rest of the detail lives in linked files)

| Topic | File |
|-------|------|
| Inherited architecture | `../python-activerecord/.claude/architecture.md` |
| Inherited code style | `../python-activerecord/.claude/code_style.md` |
| Inherited testing strategy | `../python-activerecord/.claude/testing.md` |
| Inherited version control | `../python-activerecord/.claude/rules/version_control.md` |
| Testsuite directory layout (`src/` vs `tests/`, three categories, topic / subtopic rules, fixture model versions) | `.claude/rules/testsuite_structure.md` |
| Sync / async parity (six rules, sync ↔ async mirror, provider fixture setup/teardown) | `.claude/rules/sync_async_parity.md` |
| Test case naming & markers (classes, files, methods, fixtures, capability decorators) | `.claude/rules/test_case_naming_and_markers.md` |
| Developer tools (parity / structure / naming / markers checkers under `tools/`) | `.claude/rules/development_tools.md` |

## Quick Reference

- `src/` is the import target for backend packages; backends import its
  modules via thin bridge files (`from …testsuite.feature.<topic>.test_x
  import *`) under their own `tests/rhosocial/<backend>_test/...` tree.
- `tests/` is for the testsuite's own self-tests only and is NOT
  imported by backends.
- Run tests from a backend project root (e.g. `python-activerecord/`),
  not from this directory. See
  `.claude/rules/test_case_naming_and_markers.md` §7 for verification
  commands.
- The sync/async parity checker lives at
  `tools/check_sync_async_parity.py` (implemented, along with
  `tools/check_structure.py`, `tools/check_naming.py` and
  `tools/check_markers.py` — see `tools/README.md`).
  Run all four from the repository root before opening a PR:

  ```bash
  python tools/check_sync_async_parity.py
  python tools/check_structure.py
  python tools/check_naming.py
  python tools/check_markers.py
  ```

## Documentation

- `docs/en_US/` — English (authoritative)
- `docs/zh_CN/` — Chinese

## Version Control and Changelog

Adheres to the same standards as the main `python-activerecord` project;
see `../python-activerecord/.claude/rules/version_control.md`.

## Distribution & Consumption

PyPI-served artifacts of this project are **not** the source of truth for
tools like the sync/async parity checker, the rule docs in
`.claude/rules/`, the README examples, or future pytest plugins. The
sdist/wheel published to PyPI exists primarily so that backend projects
can `pip install` the part of the suite they need to run against their
own backend.

What backend projects actually need:

- `rhosocial.activerecord.testsuite` (the importable package — i.e.
  this project's `src/`) — consumed via PyPI / `pip install`. This is
  where abstract test cases, provider interfaces, fixtures, the
  `requires_protocols` / `requires_functions` decorators, etc. live.
- Their own backend-specific code (conftest.py, provider
  implementations, bridge files in their `tests/` tree).

What is NOT shipped through the PyPI package in a meaningful way:
- `.claude/rules/` and the content driven from them.
- `tools/` — including the four checkers (`check_sync_async_parity.py`,
  `check_structure.py`, `check_naming.py`, `check_markers.py`)
  and `tools/_common.py`. These are developer-only, not runtime
  package dependencies.
- The `tests/` self-test directory (it tests the testsuite itself, not
  a backend; backends never import it).

Backend maintainers who want to run the parity checker, refresh rule
docs, or contribute new contract tests need to **clone this repository
and work on the source tree** — they should not derive these from the
distributed wheel. Treat the wheel as a runtime dependency; treat the
git checkout as a development dependency.

## Getting Help

1. Start from this project's `.claude/rules/` directory.
2. For implementation patterns, see the backends (`python-activerecord`,
   `python-activerecord-mysql`, etc.) and their `tests/` mirror trees.
3. For provider interface contracts, browse
   `src/rhosocial/activerecord/testsuite/feature/<topic>/interfaces.py`.
