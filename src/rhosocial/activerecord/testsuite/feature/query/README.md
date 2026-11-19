# Query Feature Tests

Tests for the ActiveQuery system — query building, execution, and result processing, organized
into 14 subcategories.

## Directory Layout

| Subdirectory | Content |
|-------------|---------|
| `basic/` | Core query operations — `find_all`, `find_one`, `where`, `order_by`, `limit`, `offset`, `pluck`; **composite PK query** (`test_composite_pk_query.py`) |
| `aggregate/` | Aggregate functions — `count`, `sum`, `avg`, `min`, `max`, grouped aggregation |
| `joins/` | JOIN operations — `inner_join`, `left_join`, `right_join`, `cross_join`, chained joins |
| `set_operations/` | Set operations — `UNION`, `INTERSECT`, `EXCEPT`; **composite PK set operations** (`test_composite_pk_set_operation.py`) |
| `cte/` | Common Table Expressions — recursive and non-recursive CTEs, `with_cte()`; **composite PK CTE** (`test_composite_pk_cte.py`) |
| `window_functions/` | Window functions — `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`, `LEAD` |
| `range_queries/` | Range / interval queries — date ranges, numeric ranges, inclusive/exclusive bounds |
| `eager_loading/` | Eager loading — `with_()`, nested eager loading, batch loading |
| `relations/` | Relation-based queries — through descriptors, inverse_of, self-referential |
| `error_handling/` | Error paths — invalid column names, type mismatches, unsupported operations |
| `cross_database/` | Cross-database compatibility — dialect-specific query behavior |
| `optimization/` | Query optimization — query plan inspection, index hints, `EXPLAIN` |
| `logging/` | Query logging — SQL generation logging, data summarization |
| `special/` | Special query types — raw SQL, subqueries, dynamic queries |
| `connection/` | Database connection lifecycle and configuration (shared with `basic/`) |
| `fixtures/` | Model class definitions across 4 Python versions |
| `samples/` | Sample data files for logging/summarization tests |
| `worker/` | Multi-process worker pool tests (shared with `basic/`) |

## Provider Interface

`interfaces.py` defines `IQuerySyncProvider` and `IQueryAsyncProvider`. Backend projects implement
these to supply configured model classes and database schemas.

## L2 environment and fixtures

This topic declares `DECLARATION(uses_database=True)` in `conftest.py`. L1 model
classes live in `fixtures/` (models across Python versions plus blog/json/extended/
cte model families); the L2 `conftest.py` wires `database_config` / `database` /
`schema` and exposes per-group handles — `order_fixtures`, `blog_fixtures`,
`tree_fixtures`, `json_user_fixture`, `combined_fixtures`, and their async twins.
`basic/` (in this topic) contains the composite-PK contracts, including a
`test_explain` that only asserts `explain()` is executable when the dialect
advertises `supports_explain_plan()`.

## For backends importing this topic — test EXPLAIN thoroughly

EXPLAIN differs radically across databases (syntax, options, and especially the
shape of the returned plan: tabular rows vs JSON vs `PLAN_TABLE` vs none). The
shared `test_explain` here only guarantees the clause **can execute** when
supported. Backends are expected to go further in their **local** `feature/query`
tests, using these shared fixtures to prepare a typical environment and data:

- Build tables with a primary key, single- and composite indexes, a unique
  constraint, and a foreign key; seed a few rows.
- Run `EXPLAIN` on: a simple PK/index point lookup, a two-table JOIN, and an
  aggregate (`GROUP BY` + `COUNT`/`SUM`). Assert on whatever the local dialect
  exposes — access method, index usage, scanned rows/cost — using that backend's
  own result type.
- Exercise the options the backend supports (`analyze`, `format`, `verbose`, …)
  and keep `supports_explain_*` probes consistent with reality.
- If the backend has declarative partitioning, prepare a partitioned table plus
  seed data and verify **partition pruning** evidence in the plan.
- If the dialect reports `supports_explain_plan() == False` (e.g. Firebird), skip
  the whole group via the capability gate.

Depth and assertions are intentionally backend-local — do not add a generic
result-shape contract to the testsuite.
