# `feature/cte` — CTEQuery 自身

独立 topic：只覆盖 **CTEQuery 自身** 的行为，不掺入 ActiveQuery / SetOperation 的组合场景。

## 范围

- 测试：`test_composite_pk_cte.py` / `test_composite_pk_cte_async.py`
  （复合主键模型上的 CTE 聚合、主键过滤、不支持 CTE 的后端报错）。
- L1 夹具：`fixtures/cte_models.py` / `fixtures/async_cte_models.py` 中的 `Node` / `AsyncNode`
  （树结构模型，供 `tree_fixtures` 使用）。复合主键 `OrderItem` 单向借用
  `basic/fixtures` 的公开名，不在本 topic 重复定义。
- L2 环境：`conftest.py` 自带 `DECLARATION(uses_database=True)` 及
  `database_config` / `database` / `schema`，`schema` 创建 `order_items` 与 `nodes` 两张表；
  `tree_fixtures` 是仅含 `Node` 的夹具组。

## 不在此 topic

- `test_cte_query_active_query*` / `test_cte_query_set_operation*`：三类型组合，归 `query_integration`。
- 纯 ActiveQuery 与 SetOperation 行为：分别归 `query` 与 `setop`。
