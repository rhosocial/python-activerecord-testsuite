# Test Case Naming & Marker Rules

> **AI Assistant Note**: This document is a hard rule for any contribution to
> `python-activerecord-testsuite`. It complements, but does NOT replace, the
> structural rules in `.claude/rules/testsuite_structure.md` and the parity
> rules in `.claude/rules/sync_async_parity.md`. When in doubt: structure →
> parity → naming & markers.

## 1. Scope

This document defines three orthogonal classification axes for tests:
1. **Test category** (`feature`, `benchmark`, `realworld`) — expressed via
   **directory layout**, NOT markers.
2. **Sync / async** — expressed via the dedicated `asyncio` marker for the
   async side; the sync side carries **no** extra marker.
3. **Backend-specific capability** — expressed via exactly two generic
   decorators: `requires_protocol` (for Protocol-class capabilities) and
   `requires_functions` (for SQL-function-name capabilities). **Do not
   introduce per-feature alias markers** such as `requires_partition`,
   `requires_cte`, etc., unless a clear, repeated need appears and is
   approved in a separate PR.

Anything not expressible through one of those three axes does NOT need a
marker. Resist marker inflation.

## 2. Test Category — directories, not markers

The category a test belongs to is wholly determined by its path. Do NOT
add `feature` / `benchmark` / `realworld` markers; the directory name is
already the category.

```
python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/
├── feature/    # category
├── benchmark/  # category
└── realworld/  # category
```

Each backend project (`python-activerecord`,
`python-activerecord-mysql`, etc.) imports the testsuite tests via
1-to-1 mirror tree under its own `tests/` directory, e.g.:

```text
python-activerecord/
└── tests/
    ├── conftest.py          # root conftest; sets TESTSUITE_PROVIDER_REGISTRY
    └── rhosocial/activerecord_test/
        ├── feature/
        │   ├── basic/
        │   │   ├── conftest.py
        │   │   ├── test_foo.py            # contents: `from …testsuite.feature.basic.test_foo import *`
        │   │   └── test_foo_async.py      # mirror of the above
        │   ├── composite_pk/
        │   └── ...
        └── (future)  benchmark/  realworld/
```

Inside a backend project, pytest runs from the backend's root with its
own `pyproject.toml [tool.pytest.ini_options]` (not the testsuite's).
Each leaf `tests/.../test_foo.py` is **just a thin bridge** that
imports everything from the corresponding testsuite module:

```python
# python-activerecord/tests/rhosocial/activerecord_test/feature/basic/test_foo.py
from rhosocial.activerecord.testsuite.feature.basic.test_foo import *  # noqa: F403
```

Selection by category is done by pointing pytest at the right path,
e.g. `pytest tests/rhosocial/activerecord_test/feature/basic`. The
category selector lives on the filesystem; do not register `feature`
/ `benchmark` / `realworld` as pytest markers.

## 3. Sync / Async — automatic via `asyncio_mode = "auto"`

### 3.1 Rule

- **No explicit `@pytest.mark.asyncio` is used anywhere** — neither on sync
  nor on async files. The project configures `asyncio_mode = "auto"` in
  `pyproject.toml`, which causes pytest-asyncio to automatically add the
  `asyncio` marker to every `async def test_*` function at collection time.
- Sync files (`test_*.py`) carry **no** marker. `not asyncio` is the
  implicit default for `def test_*` functions.

Rationale: under `asyncio_mode = "auto"` the explicit decorator is entirely
redundant. The marker is still usable for filtering (see §3.2) because
pytest-asyncio auto-applies it during collection, but there is no need to
write it in source. Keeping it absent eliminates ~680 boilerplate lines
across the testsuite and removes the line-count asymmetry between sync and
async files.

### 3.2 Selector examples

Examples assume you are running pytest from the backend project root
(e.g. `python-activerecord/`) which already wires
`TESTSUITE_PROVIDER_REGISTRY` via its top-level `tests/conftest.py`.
Adjust paths for other backend projects; selection logic is identical.

```bash
# Async tests only (run from python-activerecord/)
pytest tests/ -k async  # file/class/method name contains "async"

# Sync tests only
pytest tests/ -k "not async"  # exclude everything with "async" in the name

# Or use the auto-applied asyncio marker (auto mode adds it)
pytest tests/ -m asyncio
pytest tests/ -m "not asyncio"

# Topic-level selection (no marker needed; pure path)
pytest tests/rhosocial/activerecord_test/feature/partition
```

### 3.3 Removed (no-op since `@pytest.mark.asyncio` is unused)

The `@pytest.mark.asyncio` decorator and its placement rules no longer
apply. Helpers (`_*` methods) inside async classes do NOT need any marker;
their `async def` keyword is sufficient for pytest-asyncio to recognise
them as async fixtures or helpers.

### 3.4 What is NOT a marker for sync/async

- `TestAsync` prefix on classes — naming, NOT marker.
- `_async.py` suffix on filenames — naming, NOT marker.
- `async def` on test methods — syntax, NOT marker.

## 4. Backend-Specific Capability — generic `requires_protocol` / `requires_functions`

### 4.1 When to add a capability marker

Add a capability marker ONLY when the test exercises behavior that
**means different things on different backends today**, and:

- Some backends support the feature and others do not; the test must
  run as `skip` (not pass, not fail) on the unsupported ones.
- The capability is detectable through either:
  - a Protocol class on the dialect (e.g. `PartitionSupport`,
    `CTESupport`, `ReturningSupport`); use `requires_protocol`.
  - a built-in function name on the dialect's
    `supports_functions(...)` method (e.g. `json_extract_text`,
    `jsonb_array_insert`); use `requires_functions`.

Do NOT add a capability marker when:

- The feature is universal — every backend that imports the file ships
  the same answer.
- The test is already gated by an in-body
  `if not backend.supports_*: pytest.skip(...)`. In that case the inline
  skip is the source of truth; an additional marker would duplicate it
  and drift.
- The backend implements the feature but with a quirk; the quirk
  belongs in a dedicated test, not a global skip on this one.

### 4.2 The two generic decorators

There are exactly two generic capability markers. Both live in
`rhosocial.activerecord.testsuite.utils.common` and are registered
through `pytest_configure` in
`src/rhosocial/activerecord/testsuite/conftest.py`:

| Decorator | Marker name | Captures |
|-----------|-------------|----------|
| `requires_protocol(ProtocolClass, method=None)` | `requires_protocol` | Capability expressed by a dialect Protocol class (optionally a specific `supports_*` method). |
| `requires_functions(*fn_names)` | `requires_functions` | Capability expressed by SQL function name(s) the dialect must expose. |

Each expands to a single pytest marker; the runtime skip logic lives
in topic-level `conftest.py` files (e.g.
`feature/relation/conftest.py`, `feature/query/conftest.py`) which read
the markers via `request.node.get_closest_marker(...)`.

```python
from rhosocial.activerecord.backend.dialect.protocols import PartitionSupport
from rhosocial.activerecord.testsuite.utils.common import (
    requires_protocol,
    requires_functions,
)

class TestPartitionCRUD:
    @pytest.mark.asyncio
    @requires_protocol(PartitionSupport, "supports_table_partitioning")
    async def test_create_partitioned_table(self, ...):
        ...

class TestJsonExtraction:
    @requires_functions('json_extract_text', 'jsonb_array_insert')
    def test_extract_text(self, ...):
        ...
```

### 4.3 No per-feature aliases

Do **not** introduce `requires_partition`, `requires_cte`, etc. as
named wrappers around `requires_protocol`, or `requires_json`,
`requires_window_fn`, etc. as named wrappers around
`requires_functions`:

- Capability-Protocol pairs number in the dozens (`PartitionSupport`,
  `CTESupport`, `ReturningSupport`, `UpsertSupport`,
  `WindowFunctionSupport`, `JSONSupport`, `LockingSupport`,
  `TriggerSupport`, `SequenceSupport`, `GeneratedColumnSupport`,
  `ExplainSupport`, `ArraySupport`, and so on). Each has multiple
  `supports_*` methods, and the function-name list is even longer.
  Pre-declaring aliases for every node in this graph produces
  dozens-to-hundreds of registered markers, most of which will never
  be used or will be mistyped.
- BackendProtocol/Support classes and the function registry both
  evolve (new methods, renamed methods, new function names). Aliases
  would need to be re-defined in lockstep or quietly rot. The generic
  form keeps the cost of tracking this change at the call site, not in
  a marker registry.
- Filtering by capability is rare in practice. Selection usually
  happens at the file / topic level (e.g. "skip the partition topic on
  SQLite"), not at the per-method level with arbitrary `-m` strings.

If a future contributor finds a case where a tiny alias is genuinely
worth defining, raise it on a PR and update this section. Until then,
`requires_protocol` and `requires_functions` are the **only** two
capability markers.

### 4.4 Capability marker vs. inline skip

If a test carries both a capability marker and an inline
`if not backend.supports_*: pytest.skip(...)` check (or an equivalent
in-body call like `skip_test_if_protocol_unsupported(...)` /
`skip_test_if_functions_unsupported(...)`), prefer ONE form: the marker
is the source of truth for "this test requires capability X"; the body
should NOT independently re-check `supports_X()` or `supports_functions(X)`.

Use inline `pytest.skip` ONLY for scenario-local conditions (e.g.
"data variant unavailable", "scenario not configured for this backend
class") that have nothing to do with backend capability.

## 5. Naming Conventions

### 5.1 Test class names

A class counts as a **test class** if and only if at least one method
defined directly inside it is named `test_*`. The prefix rules below
apply only to test classes; helper classes (e.g. `QueryCounter`,
`MockQuery`, `ColumnNameKey`, Pydantic fixture models in
`test_pydantic_native_validation.py`) are free to use any class name.

| Side | Prefix | Examples |
|------|--------|----------|
| Sync | `Test` | `TestPartitionCRUD`, `TestUpsert` |
| Async | `TestAsync` | `TestAsyncPartitionCRUD`, `TestAsyncUpsert` |

Pairs are one-to-one in order, and class order parity is enforced by
`.claude/rules/sync_async_parity.md`. Bases and subclasses mirror:

```python
# sync
class TestRangePartitionBase: ...
class TestRangePartitionCreate(TestRangePartitionBase): ...

# async
class TestAsyncRangePartitionBase: ...
class TestAsyncRangePartitionCreate(TestAsyncRangePartitionBase): ...
```

### 5.2 Test method names

| Side | Prefix | Sub-template |
|------|--------|--------------|
| Sync | `def test_` | `test_<verb>_<topic>[_<qualifier>]` |
| Async | `async def test_` | same suffix as the sync pair |

Topic-method verbs (non-exhaustive):

```
create, insert, save, update, delete, find, find_one, count,
exists, attach, detach, bulk_create, bulk_insert, partition,
add_partition, drop_partition, reorganize_partition, attach_partition
```

Examples:

```python
def test_create_range_partition(self): ...
def test_bulk_insert_with_returning(self): ...
def test_window_function_with_partition_by(self): ...
```

A class's async twin has **identical** method names modulo the
`async def` keyword. The `_async` suffix in helper functions
(e.g. `run_async(...)`) is allowed but NEVER as a **trailing** suffix
on a test method name (e.g. `test_create_partition_async` → just
`test_create_partition`); the trailing sync/async info is redundant
because the side is encoded in the file name and class name.

The substring `_async` is allowed mid-name when it describes the *subject*
of the test rather than the *side* of the test. For example
`test_async_belongs_to_on_async_model_raises` validates that calling a
sync descriptor on an async model is rejected; the word `async` there
refers to the model / descriptor under test, not to which side of the
sync/async pair the method belongs to. The rule above forbids only the
trailing form (`test_foo_async`).

### 5.3 File names

Sync file: `test_<topic>.py` (e.g. `test_partition_crud.py`).
Async file: `test_<topic>_async.py` (e.g.
`test_partition_crud_async.py`).

Pairing is enforced by `.claude/rules/sync_async_parity.md §1`.

Topic filenames SHOULD start with the directory's topical noun. When
two directories naturally produce the same filename, prefer qualifying
with the most specific noun (e.g. `test_composite_pk_partition`) over
generic prefixes (e.g. `test_partition_with_pk`).

### 5.4 Helper / fixture names

- Sync fixtures: `xxx_fixtures` (e.g. `order_fixtures`).
- Async fixtures: `async_xxx_fixtures` (e.g. `async_order_fixtures`).
- Provider methods: `setup_*_fixtures` (sync) /
  `async_setup_*_fixtures` (async), per
  `.claude/rules/sync_async_parity.md`.

## 6. Decorator Order

Apply decorators in a stable order across the file so parity diffing
stays cheap:

1. `@pytest.mark.requires_protocols(...)` and / or
   `@pytest.mark.requires_functions(...)` (if needed).
2. `@pytest.mark.parametrize(...)` last (captures already-annotated
   functions).

Note: `@pytest.mark.asyncio` is **never used** (see §3). `asyncio_mode =
"auto"` handles async test detection automatically.

The mirror order MUST match between the sync and async halves
(`.claude/rules/sync_async_parity.md §5`).

## 7. Verification Checklist

Before submitting a change that touches naming or markers, run from the
**backend project root** (`python-activerecord/`,
`python-activerecord-mysql/`, etc.), not from this `testsuite/`
directory. The testsuite is imported by backends; it does not own a
viable pytest configuration on its own for these checks.

```bash
# 1. Pair existence — run from python-activerecord-testsuite/
python tools/check_sync_async_parity.py

# 2. Marker registration — list markers as seen by the backend.
pytest tests/ --markers 2>&1 \
    | grep -E 'requires_protocols|requires_functions|asyncio'

# 3. Filter sanity (both selectors must produce non-empty sets)
pytest tests/ -m asyncio --collect-only -q
pytest tests/ -m "not asyncio" --collect-only -q
```

## 8. Relationship to Other Rules

| Rule file | Topic | How it interacts |
|-----------|-------|------------------|
| `.claude/rules/testsuite_structure.md` | Topics, subtopics, sync/async file pairs | This document assumes the structural layout is intact. |
| `.claude/rules/sync_async_parity.md` | Six parity rules, sync ↔ async | Markers in §3 and §4 must mirror on both sides. |
| `../python-activerecord/.claude/testing.md` | Top-level testing strategy | Inherited from the core ruleset; this file is contract-specific to testsuite. |
| `src/rhosocial/activerecord/testsuite/conftest.py` | Marker registration | The `requires_protocols` and `requires_functions` markers, plus the `asyncio` marker, are registered here. |
| `pyproject.toml` `[tool.pytest.ini_options].markers` | CI marker declaration | Mirror the registration list in conftest.py to keep `--strict-markers` happy. |
