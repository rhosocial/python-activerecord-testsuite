# Basic Feature Tests

Testsuite for core ActiveRecord functionality — CRUD, field types, type adapters, validation, column mapping, and connection/worker lifecycle.

## Directory Layout

| Directory | Content |
|-----------|---------|
| `crud/` | Basic create, read, update, delete; `find_all` (no condition, dict, list-of-IDs); query builder and aggregates |
| `crud_composite_pk/` | CRUD over composite primary keys (`order_items`, `store_inventory`) and column-mapped composite keys |
| `bulk_crud/` | Bulk insert, batch update/delete, chunked operations |
| `fields/` | Field type round-trips (str, int, float, Decimal, bool, datetime, JSON, nullable, UUID PK); column mapping via `UseColumn` and `UseAdapter`; invalid annotation combinations; **derived field declaration & query** (`test_derived_field.py`) |
| `type_adapter/` | Optional type adapter (str/int/datetime/bool); custom adapter via `UseAdapter`; built-in `BooleanAdapter` raw storage verification |
| `validation/` | Pydantic `field_validator` / `model_validator`; Pydantic native validation (mutable defaults, lifecycle, coercion, literals, extra/forbid/ignore/allow) |
| `connection/` | Database connection lifecycle and configuration |
| `worker/` | Multi-process worker pool tests |
| `transaction/` | Savepoint API and cross-task transaction ownership |
| `nopk/` | Keyless models (`primary_key() -> None`) — where identity-based access must be refused |
| `readonly/` | `ReadOnlyMixin` / `IReadOnlyBehavior` — class-level and instance-level write refusal |
| `ddl/` | DDL statement-level contracts (`ALTER … IF EXISTS`, materialized view rendering) |
| `fixtures/` | **The only place model classes, adapters and DDL/DML operations are defined** — [redesign plan](fixtures/README.md) |

## Fixtures

All tests inherit fixtures from `conftest.py` at this level. Each fixture is parameterized over backend scenarios (e.g. in-memory SQLite, file-based SQLite). Tests use provider-managed models (e.g. `user_class`, `validated_user_class`, `type_test_model`, `type_adapter_fixtures`, `mapped_models_fixtures`).

**Ownership rule** — `fixtures/` is the single definition site for the `basic` scope:

- Test directories under `basic/` **must not define their own** models, adapters or DDL/DML
  operations; they keep only `pytest` fixtures and assertions. A directory `conftest.py`
  only selects tables, creates them, and hands them to the tests.
- Other features **may** consume `basic/fixtures` (today: `feature/query` uses
  `OrderItem`/`AsyncOrderItem`; `feature/cli` uses `User`, `ValidatedUser`, `BulkUser`).
  The dependency is one-way — `basic/fixtures` never imports from another feature.
- Because of that, public names here are a cross-feature contract: renaming or removing
  one requires updating the consuming `conftest.py` in the same change.

See [fixtures/README.md](fixtures/README.md) for the redesign plan (§0.1 scope,
§3.1 ownership inventory, §2 P3 Python-version axis).

## Provider Interface

`interfaces.py` defines `IBasicSyncProvider` and `IBasicAsyncProvider`. Backend projects implement these to supply configured model classes and database schemas.
