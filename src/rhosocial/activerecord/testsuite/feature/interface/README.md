# Interface Tests

Tests for low-level interface utilities consumed by the ActiveRecord query system.

## Directory Layout

| File | Sync/Async | Scope |
|------|------------|-------|
| `conftest.py` | — | Minimal pytest configuration |
| `test_threadsafe_dict.py` | both | `ThreadSafeDict` — basic operations, thread safety (concurrent set/update via `ThreadPoolExecutor`), iterator (`items()`, `keys()`, `values()`), nested dict support |
