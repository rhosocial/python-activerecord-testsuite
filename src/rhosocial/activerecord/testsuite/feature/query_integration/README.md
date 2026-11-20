# Query Integration Feature Tests

The three pairwise combinations of the query types that otherwise live in
their own topics:

| Combination | Test files |
|-------------|------------|
| CTEQuery + ActiveQuery | `test_cte_query_active_query.py`, `test_cte_query_active_query_async.py` |
| CTEQuery + SetOperationQuery | `test_cte_query_set_operation.py`, `test_cte_query_set_operation_async.py` |
| ActiveQuery + SetOperationQuery | `test_active_query_set_operation.py`, `test_active_query_set_operation_async.py` |

## Why this is an independent topic

These cases need **combination fixtures** that neither the `cte` nor the
`setop` topic owns on its own:

* the CTE + ActiveQuery cases need the `Node` **tree group** (`tree_fixtures`);
* the CTE + SetOperation and ActiveQuery + SetOperation cases need the
  `User`/`Order`/`OrderItem` **order group** (`order_fixtures`);
* both groups must be configured against **one shared database** in a single
  L2 environment.

Those fixtures are the parent `query` topic's L2 combination fixtures, not the
`DEFINITIONS` of `cte` or `setop`.  Putting the tests under either single-type
topic would force that topic to import the other's models and schemas, breaking
the "each topic owns its fixtures, no cross-topic imports" rule.  A dedicated
topic keeps the union of models (`Node` + the order group) and its
`DECLARATION(uses_database=True)` environment local, while still letting the
core repo bridge only this directory.

Each fixture group is one unit of work: all its models share a single backend
instance so query-counting assertions observe the same connection.

## For backends importing this topic — EXPLAIN is most revealing here

Combined queries expose the **largest** cross-database EXPLAIN differences.
Single-type plans mostly show "which index was used", but a CTE wrapping an
`ActiveQuery`, or a `SetOperationQuery` combining subqueries, surfaces structural
differences: how each backend represents a CTE scan (materialized vs inlined),
a UNION's dedup strategy (sort vs hash), nested plan-node types and cost models.
Postgres shows distinct `CTE Scan`/`Append` nodes, MySQL uses `DERIVED`/`UNION`
select types, Oracle emits hierarchical `PLAN_TABLE` rows, SQLite inlines the
CTE — the same combined query yields a completely different plan tree per
backend. This topic's fixtures are therefore the best vehicle for exercising
that diversity.

EXPLAIN syntax, options, and plan shape differ too much for a generic result
contract, so the testsuite does not assert on plan shape here. Backends should,
in their **local** `feature/query_integration` tests, use the `tree_fixtures` and
`order_fixtures` (both configured against one shared database) to:

- verify each combined form's `.explain().aggregate()` executes and returns a
  non-empty plan when `supports_explain_plan()` is true;
- **interpret the plan with the local result type** — CTE scan/materialization
  strategy, set-operation dedup method, nested node shapes, index usage, cost;
- exercise supported options (`analyze`, `format`, `verbose`, …) and keep
  `supports_explain_*` probes consistent;
- if a backend cannot EXPLAIN a particular combination, skip that case via the
  capability gate; a dialect reporting `supports_explain_plan() == False` skips
  the whole group.
- partition-pruning EXPLAIN, if relevant, is likewise decided per backend.

Depth and assertions stay backend-local — do not add a generic plan-shape
contract to the testsuite.
