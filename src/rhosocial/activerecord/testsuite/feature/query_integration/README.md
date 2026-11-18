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
