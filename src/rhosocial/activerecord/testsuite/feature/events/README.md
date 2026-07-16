# Event / Lifecycle Tests

Tests for the ActiveRecord event system — lifecycle hooks (before/after insert, update, delete,
validate) and event handler registration.

## Directory Layout

| File | Description |
|------|-------------|
| `conftest.py` | Scenario parameterization via `IEventsSyncProvider` / `IEventsAsyncProvider` |
| `interfaces.py` | `EventsProviderBase` — requires `event_model` |
| `fixtures/models.py` | Model definitions (`EventModel`, `EventLogModel`) across 4 Python versions |

### Test Files

| File | Sync/Async | Scope |
|------|------------|-------|
| `test_handlers.py` | both | `on()` registration, handler invocation for `BEFORE_INSERT`, `AFTER_INSERT`, etc. |
| `test_lifecycle.py` | both | Lifecycle event ordering — validates correct sequence: `BEFORE_VALIDATE → AFTER_VALIDATE → BEFORE_INSERT → AFTER_INSERT`; update and delete cycles |
