# `feature/setop` — SetOperationQuery 自身

独立 topic，承载 `SetOperationQuery` / `AsyncSetOperationQuery` 自身的契约测试
（不含 ActiveQuery × SetOperation 组合测试，那些归 `query_integration`）。

## 内容

| 路径 | 用途 |
|------|------|
| `conftest.py` | 自带 `DECLARATION(uses_database=True)` + L2 数据库/`schema` 环境；`order_fixtures` / `async_order_fixtures`（User/Order/OrderItem `BackendGroup`）；`order_item_class` / `async_order_item_class`（借 basic 公开的复合主键 OrderItem） |
| `fixtures/models.py` | Python 3.8 基线：User / Order / OrderItem（仅保留 setop 用到的类） |
| `fixtures/async_models.py` | 上述三者的 async 孪生 |
| `fixtures/models_py310.py` / `py311.py` / `py312.py` | 按解释器版本选取的模型副本（同样只保留 User/Order/OrderItem） |
| `fixtures/definitions.py` | 三张表（users / orders / order_items）的 DDL 定义，供 `schema` fixture 使用 |
| `test_set_operation*.py` | 同步/异步 set operation 自身测试 |
| `test_composite_pk_set_operation*.py` | 复合主键模型上的 UNION / INTERSECT / EXCEPT 测试 |

## 夹具来源

- L1 order 模型组从原 `query/fixtures/models.py` 拆出并精简；不跨 topic import。
- 复合主键测试用的 `order_item_class` 单向借 `basic.fixtures.models.OrderItem`
  的公开名，不在本 topic 重复定义。
- `order_items` 表 DDL 是 setop OrderItem 与 basic 复合主键 OrderItem 的超集。

## 后端引入时：充分测试 set operation 的解释子句能力

UNION / INTERSECT / EXCEPT 的 `EXPLAIN` 在各库差异极大（语法、选项、返回结构 ——
表格行 / JSON / SHOWPLAN / PLAN_TABLE 等），testsuite 不提供通用的结果解读契约。
引入本 topic 的后端，请用 `order_fixtures` / `fixtures/definitions.py` 的三表
（users / orders / order_items）在**本地** `feature/setop` 补充分测试：

- 在支持 `supports_explain_plan()` 的方言上，验证
  `SetOperationQuery.explain().aggregate()` 能执行并返回非空计划；
- 用示例数据构造 UNION / INTERSECT / EXCEPT，执行 `EXPLAIN` 并按本库结果类型
  解读（分支扫描方式、去重策略、索引命中、代价等）；
- 覆盖本库支持的选项（`analyze` / `format` / `verbose` 等），保持
  `supports_explain_*` 探针与实际一致；
- 若本库不支持某种 set operation 或不可对其 EXPLAIN，按能力门跳过；方言报告
  不支持时整组跳过。
- 是否测试分区裁剪解释、如何解读，完全由后端按自身分区能力自行决定。

深度断言一律留在后端本地，不要加入 testsuite 通用契约。
