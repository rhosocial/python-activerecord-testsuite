# Sync / Async Test Parity Rules

> **AI Assistant Note**: This document is a hard rule for any contribution to
> `python-activerecord-testsuite`. Any change that violates these rules MUST be
> fixed in the same commit. Run `python tools/check_sync_async_parity.py` (or
> the equivalent sequence shown below) before claiming parity.

## Goal

Every backend-agnostic test in `src/rhosocial/activerecord/testsuite/` that
exists for the synchronous API MUST also exist — logically equivalent — for
the asynchronous API, and vice versa. The two halves (sync, async) must be
mirror images of each other so that a reader can read either file alone and
fully understand what is being verified.

The pairing is structural, not behavioural: any capability-skip, error
message, side-effect, or assertion that exists on one side MUST exist on the
other side **in the same order**, with the same wording where possible.

## Scope

- Applies to every `test_*.py` file under
  `src/rhosocial/activerecord/testsuite/` whose filename starts with `test_`
  AND which references models/queries/operations that have a sync and async
  API surface.
- Does **not** apply to:
  - `conftest.py`, `interfaces.py`, helper modules, fixture modules.
  - Files that intentionally test only sync or only async (rare; if added,
    document the reason in the file header).
  - Directories whose `conftest.py` declares a non-default `__parity__` mode
    (see [Per-directory parity mode](#per-directory-parity-mode-__parity__) below).

## Backend Provider (interfaces.py) Sync/Async Rules

Every `feature/<topic>/interfaces.py` (and every
`benchmark/<topic>/interfaces.py`) defines the provider contract that
backend packages implement.

### Setting up and tearing down fixtures

- The provider interface MUST declare setup and teardown hooks as **paired**
  methods, separately for sync and async APIs:
  - `setup_*_fixtures(...)`  ↔  `teardown_*_fixtures(...)`
  - `async_setup_*_fixtures(...)`  ↔  `async_teardown_*_fixtures(...)`
- A backend that supports only sync implements the sync pair and raises
  `NotImplementedError` (or @abstractmethod) for the async pair; the
  import surface for that backend then imports **only the sync files**
  and the async suite is `pytest.importorskip`-ed at conftest level.
- A backend that supports only async mirrors the rule with the roles
  swapped.
- A backend that supports both MUST implement both pairs; this is the
  default expectation.

### Importing the suite selectively

`conftest.py` (or the backend's `tests/conftest.py`) must import either
the sync files or the async files (or both) based on the backend's
capability. NEVER auto-import both pairs when the backend cannot run
both, since the unsupported side will produce hard runtime errors and
not `pytest.skip`.

Example conftest pattern:

```python
import pytest
from ...your_backend_capabilities import supports_async

if not supports_async():
    collect_ignore_glob = ["**/*_async.py"]
```

### Connection lifecycle — common pitfall

When implementing setup/teardown for sync vs async:

| Concern | Sync version | Async version |
|---|---|---|
| Backend handle | `Backend(config).connect()` / `.disconnect()` | `await AsyncBackend(config).connect()` / `await disconnect()` |
| Awaiting a coroutine | NEVER `await` inside sync setup/teardown | Every I/O call MUST be `await`-ed |
| Sync APIs in async | `time.sleep`, blocking driver calls — DEADLOCKS the loop | N/A |
| Async APIs in sync | Returning a coroutine without `await` — silent ignore | N/A |
| Connection close on error path | `try/finally` with `disconnect()` | `try/finally` with `await disconnect()` |
| Worker / pool shutdown | `pool.shutdown(wait=True)` | `await pool.shutdown_and_wait()` (or equivalent coroutine) |

Concrete patterns the providers MUST follow:

```python
# Sync pair (in MySQLQueryProvider, SQLiteQueryProvider, etc.)
def setup_order_fixtures(self, scenario):
    backend = Backend(config)
    backend.connect()                 # sync .connect()
    try:
        User.configure(backend)
        Order.configure(backend)
        self._execute_schema(...)
        return (User, Order)
    except Exception:
        backend.disconnect()          # sync .disconnect() in error path
        raise

def teardown_order_fixtures(self, scenario):
    backend = User.backend()          # sync getter
    backend.disconnect()              # sync cleanup
```

```python
# Async pair (in the same backend's AsyncXxxProvider)
async def async_setup_order_fixtures(self, scenario):
    backend = AsyncBackend(config)
    await backend.connect()           # MUST await — sync .connect() will deadlock
    try:
        AsyncUser.configure(backend)
        AsyncOrder.configure(backend)
        await self._execute_schema(...)
        return (AsyncUser, AsyncOrder)
    except Exception:
        await backend.disconnect()    # MUST await on error path
        raise

async def async_teardown_order_fixtures(self, scenario):
    backend = AsyncUser.backend()
    await backend.disconnect()        # MUST await cleanup
```

Critical rules that have historically caused hangs / leaks:

1. NEVER call `backend.connect()` (sync) from async code. The async
   `AsyncBackend` is a distinct object with `await connect()`.
2. NEVER `await backend.disconnect()` in sync code — there is no
   coroutine to await there.
3. NEVER swallow exceptions in finally without at least logging. A
   silent failed `.disconnect()` makes subsequent tests reuse stale
   connections.
4. NEVER start a worker pool / thread pool in async `setup_*` and
   `shutdown()` it via the sync method — the sync `shutdown(wait=True)`
   blocks the loop; use the async `shutdown_and_wait()` (or project
   equivalent).
5. NEVER share a connection between sync and async code paths within
   the same test run. Each side has its own backend instance, its own
   connection pool, and (by convention) its own on-disk file when
   SQLite file-backed.
6. The same <topic>/interfaces.py file holds BOTH the sync and async
   abstract methods. Both must be declared together so backend authors
   see the full contract.

### Why these rules matter

Mistakes here tend to either:

- Hang the pytest worker forever (sync `connect()` called from async
  setup, or sync `pool.shutdown()` from async teardown).
- Leak transient SQLite/MySQL/Postgres files / connections / handles.
- Cause flaky failures caused by stale connections being reused by the
  next test.

These are the dominant failure modes during the most recent
sync/async-parity refactors in `python-activerecord-testsuite` and
the topic-level provider/interfaces split is the boundary at which they
must be enforced.

## The Six Parity Rules

For every sync/async pair of test files (`foo.py` and `foo_async.py`):

1. **File-level pairing**
   - If `foo.py` exists, `foo_async.py` MUST exist in the **same directory**
     and **vice versa**.
   - **Exception**: Directories with `__parity__ = "async_only"` or
     `__parity__ = "sync_only"` in their `conftest.py` are exempt — unpaired
     files are expected.
   - The first-line path comment on the sync file
     (`# src/rhosocial/activerecord/testsuite/<dir>/<file>.py`)
     MUST be mirrored on the async file with the actual async path
     (`.../foo_async.py`). The leading two segments are identical; only the
     tail differs by the `_async` suffix.

2. **Class-level pairing**
   - Synchronous test class names start with `Test`. Their async siblings
     start with `TestAsync`.
   - `class TestFoo(...)`  ↔  `class TestAsyncFoo(...)`
   - Classes inside one file MUST correspond 1-to-1, in the same order, to
     classes in the paired file.
   - Subclass relationships (e.g. between a base boundary class and a
     specialised class) MUST mirror: if the sync file derives `TestBar` from
     `TestBase`, the async file derives `TestAsyncBar` from `TestAsyncBase`.

3. **Docstring pairing**
   - Module, class and test-method docstrings MUST exist on both sides.
   - Wording MAY differ, but the line count of each docstring block MUST be
     the same in the sync and async versions. (Triple-quoted blocks that are
     one logical sentence but span multiple physical lines are still counted
     line-by-line.)
   - If you want to reword, keep the number of lines identical.

4. **Order pairing inside each class**
   - The sequence of method definitions inside `TestFoo` MUST match the
     sequence inside `TestAsyncFoo`. Method N on the sync side MUST be the
     semantic counterpart of method N on the async side.
   - Helper / fixture / private methods (`_*`) inside the class follow the
     same order rule.
   - Test method names are **identical** between sync and async (e.g.
     `test_create_user` ↔ `test_create_user`). Only the method signature
     changes: `def` → `async def`, and fixture/model parameters use
     the async-prefixed variant.

 5. **Logic pairing per test**
    - For each paired test method:
      - `asyncio_mode = "auto"` is configured in `pyproject.toml`, so
        `@pytest.mark.asyncio` is **never used** in this project — neither
        on sync nor async files. Do not add it.
      - The method signature MUST differ only in: `async def`, the fixture
        name (`xxx_fixtures` → `async_xxx_fixtures`), and the model names
        (`User` → `AsyncUser`). The rest of the parameter list is identical.
      - The body MUST correspond line-for-line in the following sense:
        - Comment lines, blank lines and assignment lines MAY differ in
          variable names (sync → async prefix) but MUST keep the same number
          of lines.
        - Asserts: the same `assert` expressions with the same `msg=` text
          (or skip message) MUST appear. The only allowed substitutions are
          sync-API → async-API tokens (`query()` calls / `save()` calls /
          `await` insertion / `async` prefix on class names).
        - Exception blocks (`with pytest.raises(...)`, `try/except`) MUST
          match on type, message format and expected error class.
      - Capability skips (`@requires_protocol`, `@requires_capability`,
        `pytest.skip(...)`, `if not backend.supports_*:...`) MUST mirror:
        if sync skips for capability X, async must skip for the same
        capability X with an equivalent message.
    - Rule of thumb: diffing the two files with sync-API tokens stripped
      should show **no structural diff**.

6. **File-level line count**
    - The total number of physical lines in `foo.py` and `foo_async.py` MUST
      be close. After removing `@pytest.mark.asyncio` (redundant under
      `asyncio_mode = "auto"`), async files no longer carry extra decorator
      lines. The only remaining differences are:
      - `async` / `await` keywords (same line count unless wrapping occurs).
      - Fixture / model name substitutions (`AsyncUser` has 5 more chars than
        `User`, but they fit on the same line).
    - The parity checker allows a tolerance of ±40 lines (P6_file_lines) to
      account for blank-line normalization and fixture-model class differences.
      A violation means the file pair has a genuine structural disparity.

## Per-directory parity mode (`__parity__`)

Directories can declare their sync/async parity intent via a module-level
`__parity__` variable in the directory's `conftest.py`. The parity checker
(`tools/check_sync_async_parity.py`) reads this variable to decide whether to
enforce strict pairing.

```python
# conftest.py
__parity__ = "async_only"
```

| Value | Effect |
|---|---|
| `"sync_async"` (default) | Full enforcement — every file MUST have a counterpart (Rule 1). |
| `"async_only"` | Unpaired sync or async files do not trigger P1 orphans. If both variants exist for the same stem, P2–P6 are still checked. Use for directories where only async tests are meaningful (e.g. FastAPI benchmarks). |
| `"sync_only"` | Symmetric to `"async_only"`. Use for directories where only sync tests are meaningful. |

This mechanism avoids the need for ad‑hoc exclusion lists in the checker
script — every directory is self‑describing.

## Workflow

### Adding a new test

1. Decide whether the directory should be `"sync_async"`, `"async_only"`, or
   `"sync_only"`. If the directory's `conftest.py` does not yet have a
   `__parity__` declaration, add one.
2. Create the sync test first in the appropriate directory under
   `src/rhosocial/activerecord/testsuite/`.
3. Immediately create `test_<name>_async.py` next to it. Copy the file,
   then run a search/replace pass:
   - Add `_async` to mapping where the project convention dictates
     (filename basename, model class, fixture name, method names).
   - Add `async` keyword + `await` tokens where required.
4. Run the parity check before committing.

### Modifying an existing test

- When editing a test method, mirror the change identically in the paired
  file. Do not "modernise" only one side.
- When adding a new test method, insert it in the same position on both
  sides.
- When re-indenting or reflowing a docstring, preserve line count so the
  two files remain the same length.

## Verification

There is a parity checker script: `tools/check_sync_async_parity.py`.
It walks `src/rhosocial/activerecord/testsuite/`, finds
`(foo.py, foo_async.py)` pairs, and verifies rules 1–6. CI blocks on a
zero-violations exit.

Manual spot-check (one feature):

```bash
# Line count should be close (no @pytest.mark.asyncio on either side)
wc -l src/.../feature/basic/test_crud.py \
      src/.../feature/basic/test_crud_async.py

# Classes equal in name and order?
grep -E '^class ' src/.../feature/basic/test_crud.py \
                  src/.../feature/basic/test_crud_async.py

# Test methods equal in order?
grep -E '^    def test_|^    async def test_' src/.../feature/basic/test_crud.py \
                                             src/.../feature/basic/test_crud_async.py
```

## Known Exceptions (kept as a tracked list)

- `benchmark/fastapi` — async-only (`__parity__ = "async_only"`).
  FastAPI is an async-native framework; sync benchmarks are not meaningful.

## Triage / Fixing a Violation

1. Run the checker. Read the violation report.
2. Pick a side (sync or async) as the source of truth. The sync file is the
   usual source because it was authored first.
3. Apply the missing / divergent block to the other side, preserving
   order, line count and docstring line count.
4. Re-run the checker until exit code is 0.
5. Run pytest with the project venv:

   ```bash
   # python-activerecord virtual environment
   PYTHONPATH=src ../python-activerecord/.venv/bin/pytest \
     src/rhosocial/activerecord/testsuite/ -q
   ```
