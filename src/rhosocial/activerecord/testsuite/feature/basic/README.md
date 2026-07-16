# Basic Feature Tests

Testsuite for core ActiveRecord functionality — CRUD, field types, type adapters, validation, column mapping, and connection/worker lifecycle.

## Directory Layout

| Directory | Content |
|-----------|---------|
| `crud/` | Basic create, read, update, delete; `find_all` (no condition, dict, list-of-IDs); query builder and aggregates; **composite PK CRUD** (`test_composite_pk_crud.py`) |
| `bulk_crud/` | Bulk insert, batch update/delete, chunked operations |
| `fields/` | Field type round-trips (str, int, float, Decimal, bool, datetime, JSON, nullable, UUID PK); column mapping via `UseColumn` and `UseAdapter`; invalid annotation combinations; **derived field declaration & query** (`test_derived_field.py`) |
| `type_adapter/` | Optional type adapter (str/int/datetime/bool); custom adapter via `UseAdapter`; built-in `BooleanAdapter` raw storage verification |
| `validation/` | Pydantic `field_validator` / `model_validator`; Pydantic native validation (mutable defaults, lifecycle, coercion, literals, extra/forbid/ignore/allow) |
| `connection/` | Database connection lifecycle and configuration |
| `worker/` | Multi-process worker pool tests |
| `fixtures/` | Model class definitions across 4 version files (`models.py` 3.8+, `models_py310.py`, `models_py311.py`, `models_py312.py`) — [details](fixtures/README.md) |

## Fixtures

All tests inherit fixtures from `conftest.py` at this level. Each fixture is parameterized over backend scenarios (e.g. in-memory SQLite, file-based SQLite). Tests use provider-managed models (e.g. `user_class`, `validated_user_class`, `type_test_model`, `type_adapter_fixtures`, `mapped_models_fixtures`).

## Provider Interface

`interfaces.py` defines `IBasicSyncProvider` and `IBasicAsyncProvider`. Backend projects implement these to supply configured model classes and database schemas.
