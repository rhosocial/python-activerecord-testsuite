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
| `field_generation/` | Pure-Python field generators: per-operation value fill / write-set filter. **Declares no database.** |
| `fixtures/` | **The only place model classes, adapters and DDL/DML operations are defined** — [redesign plan](fixtures/README.md) |

## Fixtures

Fixtures live at three levels:

- **L0 `fixtures/`** — model classes, adapters and DDL/DML operations. `resolve()` picks the
  newest Python-version file that defines a name; everything else falls back to `models.py`.
- **L1 `conftest.py` (this file)** — model-handle fixtures (`user_class`, `product_class`,
  `mapped_models_fixtures`, …). Each configures a model against the directory's connection
  config and disconnects it on teardown. Tests see fixture names, not versioned model files.
- **L2 `<subdir>/conftest.py`** — `DECLARATION` plus `database_config` / `database` / `schema`.

Backend scenarios are supplied by each backend's `backend_scenario` fixture (parameterized);
a directory's tests inherit that parametrization through the `database` fixture.

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

## Database declaration (opt-in)

A test scope touches a database **only if its directory declares it**:

```python
DECLARATION = Declaration(
    uses_database=True,   # <- the single switch
    parallel=True,
    ...
)
```

- Declared scopes provide `database` / `schema` fixtures; `schema` is autouse and resets
  tables per test. `basic/ddl` declares it for a connected, adapted dialect (no tables).
- Undeclared scopes (`expressions/`, `field_generation/`) define no DB fixtures at all and
  open no connection. The plugin's collection check fails loudly if a test there starts
  requesting `database` / `schema` / `database_config`.
- Declaration is directory-level: adding a pure-Python test to a declared scope still opens
  that scope's database. Put DB-free tests in an undeclared directory.

## Backend wiring

A backend consumes this scope with two thin layers: its `basic/conftest.py` star-imports this
file, and each `<subdir>/conftest.py` star-imports the matching testsuite conftest. Test
bodies are bridged with `from rhosocial.activerecord.testsuite.feature.basic.<dir>.test_x
import *` — there is one copy of every test. No provider interfaces are involved.
