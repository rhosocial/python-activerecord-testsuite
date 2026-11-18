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
