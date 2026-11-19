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

## 后端引入时：充分测试 CTE 的解释子句能力

CTE 的 `EXPLAIN` 在各库差异极大（语法、选项、返回结构各不相同），testsuite
不提供通用的结果解读契约。引入本 topic 的后端，请用本目录的 `tree_fixtures` /
`Node` 夹具在**本地** `feature/cte` 补充分测试：

- 在支持 `supports_explain_plan()` 的方言上，验证 `CTEQuery.explain().aggregate()`
  能执行并返回非空计划；
- 用 `Node` 树结构数据构造递归/非递归 CTE，执行 `EXPLAIN` 并按本库结果类型
  解读（CTE 扫描方式、递归迭代、索引命中、代价等）；
- 覆盖本库支持的选项（`analyze` / `format` / `verbose` 等），保持
  `supports_explain_*` 探针与实际一致；
- 若本库对 CTE _plan 有特殊限制（如某些 CTE 形态不可 EXPLAIN），按能力门跳过；
  方言报告不支持时整组跳过。
- 是否测试分区裁剪解释、如何解读，完全由后端按自身分区能力自行决定。

深度断言一律留在后端本地，不要加入 testsuite 通用契约。
