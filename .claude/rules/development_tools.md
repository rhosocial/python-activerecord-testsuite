# Developer Tools Blueprint

This document lists the developer tools expected to live under `tools/`.
Each tool exists to **mechanically enforce** one or more rules
documented in `.claude/rules/`.

> **Status**: All four tools below are implemented and pass on the
> current testsuite tree (exit 1 with violation reports, exit 0 if
> clean). New violations introduced during development will be flagged.

## Tool Index

| Script | Rule(s) enforced | Status |
|--------|------------------|--------|
| `tools/check_sync_async_parity.py` | `.claude/rules/sync_async_parity.md` (six parity rules) | ✅ Implemented |
| `tools/check_structure.py` | `.claude/rules/testsuite_structure.md` (category layout, subtopic depth, required files per topic) | ✅ Implemented |
| `tools/check_naming.py` | `.claude/rules/test_case_naming_and_markers.md` §5 (class / file / fixture naming) | ✅ Implemented |
| `tools/check_markers.py` | `.claude/rules/test_case_naming_and_markers.md` §3 / §4 (`asyncio` marker position, `requires_protocol` / `requires_functions` usage) | ✅ Implemented |

## 1. `tools/check_sync_async_parity.py`

Promised by `.claude/rules/sync_async_parity.md` §"Verification" and by
`.claude/rules/test_case_naming_and_markers.md` §7.

Responsibilities:

- Walk `src/rhosocial/activerecord/testsuite/` for `test_*.py` /
  `test_*_async.py` pairs in the same directory.
- Verify for every pair:
  1. Both sides exist; neither side has an orphan sibling.
  2. Class lists (`Test…` ↔ `TestAsync…`) match in count and order;
     subclass graph mirrors sync ↔ async.
  3. Module / class / method docstring line counts are equal per pair.
  4. Method definitions inside each class appear in the same order;
     test method names are identical (only `def`→`async def` differs).
  5. Capability markers (`requires_protocols`, `requires_functions`)
     and inline skip decorations appear in the same order and same
     message; capability-mirror parity holds.
   6. Line counts are close (within ±40 lines); async files no longer
      carry extra `@pytest.mark.asyncio` decorator lines since
      `asyncio_mode = "auto"` handles async detection automatically.

Exit code 0 on full parity, 1 with a per-rule violation report
otherwise.

## 2. `tools/check_structure.py`

Promised by `.claude/rules/testsuite_structure.md`.

Responsibilities:

- Walk the three categories (`feature/`, `benchmark/`, `realworld/`).
- Verify, per category and per topic:
  - No file lives directly under a category root (every test must sit in
    a topic).
  - Topic tree depth never exceeds `category/topic/subtopic`.
  - Each topic with at least one `test_*.py` has `conftest.py`,
    `interfaces.py`, and a `fixtures/` package with at least
    `models.py` (baseline).
  - Subtopics reuse the parent topic's `fixtures/` and do not redefine
    their own `interfaces.py` base unless explicitly allowed.
- Report missing required files with their expected path so the fix is
  obvious.

## 3. `tools/check_naming.py`

Promised by `.claude/rules/test_case_naming_and_markers.md` §5.

Responsibilities:

- For every `test_*.py` file: filename pattern is `test_<topic>.py`
  (sync) or `test_<topic>_async.py` (async); no other suffixes
  (`_concurrent`, `_py3`, etc.).
- For every test class: prefix is `Test` (sync) or `TestAsync` (async);
  pairs `TestFoo` ↔ `TestAsyncFoo` (one-to-one in same file pair).
- For every test method: prefix `test_` only; method names are
  identical across the sync / async pair.
- For every fixture (`def xxx_fixtures(…)`): the async counterpart
  is `async_xxx_fixtures(…)` and vice versa; `setup_*_fixtures` ↔
  `async_setup_*_fixtures` mirroring for provider methods.
- Report each violation with `path:line` so the contributor can jump
  straight to the fix.

## 4. `tools/check_markers.py`

Promised by `.claude/rules/test_case_naming_and_markers.md` §3 and §4.

Responsibilities:

- For every test method:
  - `@pytest.mark.asyncio` MUST NOT appear anywhere (neither sync nor
    async files), because `asyncio_mode = "auto"` (set in
    `pyproject.toml`) handles async test detection automatically.
    Any stray occurrence is flagged as `M1_asyncio_unexpected`.
- For capability markers:
  - Two and only two generic capability markers exist:
    `requires_protocols` and `requires_functions`.
  - Reject any `requires_<x>` (`requires_partition`, `requires_cte`,
    `requires_json`, …) at module- or class-level scope unless it is
    declared in the short allowed list in
    `.claude/rules/test_case_naming_and_markers.md` §4.3.
  - Verify the corresponding `pytest_configure` registration in
    `src/rhosocial/activerecord/testsuite/conftest.py` and the
    `pyproject.toml [tool.pytest.ini_options].markers` list stay in
    sync.
- For tests with `requires_protocols`: the first argument must be a
  Protocol class (subclass of `Protocol`), and if `method` is given it
  must be the literal string of an attribute on that class.
- For tests with `requires_functions`: each name must be a string and
  must match `^[a-z_][a-z0-9_]*$`.

## CI Wiring

All four checkers are implemented. CI should run them on every PR
touching `src/rhosocial/activerecord/testsuite/` or `tools/`:

```bash
python tools/check_sync_async_parity.py
python tools/check_structure.py
python tools/check_naming.py
python tools/check_markers.py
```

## Adding a New Tool

1. Add a row to the table above (Status: TODO) and a short section
   matching the `## N. <name>` style.
2. Implement the script in `tools/`.
3. Update `.claude/rules/development_tools.md` if the cross-reference
   to a rule changes.
4. Update `CLAUDE.md` "Quick Reference" if the script becomes part of
   the standard verification checklist.
