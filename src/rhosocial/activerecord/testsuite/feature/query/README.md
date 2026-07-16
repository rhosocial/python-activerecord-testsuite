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
