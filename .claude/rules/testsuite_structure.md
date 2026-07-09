# Testsuite Directory Structure Rules

> **AI Assistant Note**: This document is a hard rule for any contribution to
> `python-activerecord-testsuite`. Any addition, move, or removal of test files
> MUST follow these rules.

## 1. Responsibilities of `src/` vs `tests/`

```
python-activerecord-testsuite/
├── src/    # content for backends to import (not testsuite's own tests)
└── tests/  # testsuite's own self-tests (e.g. unit tests for utils/)
```

- `src/rhosocial/activerecord/testsuite/` is the import target for backend
  packages. A backend's `tests/` directory pulls test files from here via
  pytest's `collect_ignore_glob` or explicit imports.
- `tests/` contains self-tests for the testsuite project itself and is not
  exposed to backends.

## 2. Three Test Categories

```
src/rhosocial/activerecord/testsuite/
├── feature/    # core feature tests — backends MUST import
├── benchmark/  # performance and load benchmarks — optional
└── realworld/  # complex real-world scenarios — optional
```

### Import Requirements

| Category | Backend Import | Description |
|----------|---------------|-------------|
| `feature/` | **Required** | Validates correct implementation of core features |
| `benchmark/` | Optional | Performance profiling, stress tests |
| `realworld/` | Optional | End-to-end validation of complex scenarios (currently empty) |

## 3. Test Topic

Each category (`feature/`, `benchmark/`, `realworld/`) contains subdirectories;
each subdirectory is a **test topic**.

### 3.1 Topic Nesting Limit

```
feature/
├── basic/            # OK: topic (first-level subdirectory)
│   ├── test_crud.py
│   ├── connection/   # OK: subtopic (one level deeper, no further nesting)
│   │   └── test_xxx.py
│   └── worker/       # OK: subtopic (one level deeper, no further nesting)
│       └── test_xxx.py
├── query/            # OK: topic
│   ├── test_basic.py
│   ├── connection/   # OK: subtopic
│   └── worker/       # OK: subtopic
└── ...
```

- **At most two levels**: `category/topic/` or `category/topic/subtopic/`.
- `category/topic/subtopic/subsubtopic/` or deeper nesting is **not allowed**.
- Subtopics share all common resources from the parent topic.

### 3.2 Shared Resources Within a Topic

Each topic is a self-contained test unit containing the following shared
resources:

```
feature/<topic>/
├── conftest.py       # topic-level pytest config (fixture registration, skip logic)
├── interfaces.py     # backend interface classes (ABCs defining fixture generation contracts)
├── fixtures/         # topic-shared fixture model classes
│   ├── __init__.py
│   ├── models.py          # default version (Python 3.8 baseline)
│   ├── models_py310.py    # Python 3.10+ features version
│   ├── models_py311.py    # Python 3.11+ features version
│   ├── models_py312.py    # Python 3.12+ features version
│   └── ...                # extend with more version files as needed
├── test_foo.py            # sync test
├── test_foo_async.py      # async test
└── subtopic/              # optional: one-level subtopic
    ├── conftest.py
    ├── interfaces.py      # may define subtopic-specific interfaces (inheriting parent)
    └── test_*.py / test_*_async.py
```

**Rules**:
- Subtopics **reuse** the parent topic's `fixtures/`.
- Subtopics may define **their own** `conftest.py` and `interfaces.py`
  (if subtopic-specific interface needs arise, they should inherit from the
  parent topic's interfaces).
- Subtopics MUST NOT subdivide further.

## 4. Test File Rules

### 4.1 Sync/Async Parity

Every test file is paired sync/async:

```
test_crud.py        ↔  test_crud_async.py
test_query.py       ↔  test_query_async.py
```

Full rules in `.claude/rules/sync_async_parity.md` (six parity rules).

### 4.2 Backend Import Modes

Backends may import based on their capabilities:

- **Import all**: bring in both sync and async test files.
- **Sync only**: backend supports only sync API (exclude async files via
  `collect_ignore_glob = ["**/*_async.py"]`).
- **Async only**: backend supports only async API (exclude sync files).

Imports may use:
- **Named imports**: `from ...feature.basic import test_crud`
- **Wildcard imports**: `from ...feature.basic import *`

Both are acceptable; the choice depends on the backend's `tests/conftest.py`
design.

## 5. Test Case Guidelines

### 5.1 Simplicity

Test case logic should **not be overly complex**. Each test method should:
- Focus on a single verification point.
- Avoid deep nesting or complex conditional branches.
- Separate fixture preparation from execution logic (fixture logic lives in
  the provider defined in `interfaces.py`).

### 5.2 Self-Contained Readability

Although sync/async parity is enforced, each file should be **readable and
understandable independently**. A reader should fully understand the test
intent from either the sync or the async file alone.

## 6. Fixture Model Class Version Adaptation

### 6.1 Version-Specific Files

Fixture model classes must support Python 3.8 through 3.15. Version-specific
model files provide this:

| File | Python Version | Description |
|------|---------------|-------------|
| `models.py` | 3.8+ | Default baseline version |
| `models_py310.py` | 3.10+ | Uses PEP 604 features like `Union[X, Y]` over `Optional[X]` |
| `models_py311.py` | 3.11+ | Uses PEP 673/675 features like `Self`, `StrEnum`, `LiteralString` |
| `models_py312.py` | 3.12+ | Uses PEP 695/698 features like `type` alias syntax, `@override` |

### 6.2 Backend Selection Logic

Backends select the appropriate model file based on the running Python 3
version:

```python
# Typical version selection logic in a backend's conftest.py
import sys

if sys.version_info >= (3, 12):
    from ...testsuite.feature.basic.fixtures.models_py312 import User, Order
elif sys.version_info >= (3, 11):
    from ...testsuite.feature.basic.fixtures.models_py311 import User, Order
elif sys.version_info >= (3, 10):
    from ...testsuite.feature.basic.fixtures.models_py310 import User, Order
else:
    from ...testsuite.feature.basic.fixtures.models import User, Order
```

### 6.3 Adding a New Version Branch

When adding support for a new Python version:
- Create a new `models_py3XX.py` file (only when that version's syntax or
  features are actually needed).
- Existing test files require no changes (they use models through
  `interfaces.py` and do not depend on version files directly).

## 7. New Topic Checklist

When creating a new topic, the following minimal set MUST be created:

```
feature/<new_topic>/
├── conftest.py       # required: pytest config
├── interfaces.py     # required: defines I<NewTopic>Provider (ABC)
├── fixtures/
│   ├── __init__.py   # required: makes fixtures/ a package
│   └── models.py     # required: at least the Python 3.8 baseline models
├── test_xxx.py       # at least one sync test
└── test_xxx_async.py # the matching async test
```

If the new topic needs a subtopic:

```
feature/<new_topic>/<subtopic>/
├── conftest.py       # optional: subtopic-specific config
├── interfaces.py     # optional: subtopic-specific interfaces (inheriting parent)
├── test_xxx.py
└── test_xxx_async.py
```

## 8. Relationship to Other Rules

| Rule | File | Relationship |
|------|------|-------------|
| Sync/Async Parity | `.claude/rules/sync_async_parity.md` | §4.1 references this; six parity rules govern each file pair |
| Code Style | `.claude/code_style.md` → `../python-activerecord/.claude/code_style.md` | This document does not override code style details |
| Version Control | `.claude/rules/version_control.md` | This document does not override changelog/versioning policy |