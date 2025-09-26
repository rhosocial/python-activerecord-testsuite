# 运行测试

本指南解释了如何使用测试套件执行测试。

## 1. 运行功能测试

本节详细介绍了如何运行 `feature` 测试。`basic` 目录下的测试涵盖了 ActiveRecord 的基本功能，包括：

-   **CRUD 操作**：创建、读取、更新和删除记录（`test_crud.py`）。
-   **字段类型处理**：验证各种数据类型（字符串、数字、布尔值、日期时间、JSON 等）（`test_fields.py`）。
-   **数据验证**：包括通过 Pydantic 进行的字段级验证和自定义业务规则验证（`test_validation.py`）。

### Schema 定义和夹具

测试套件定义了数据库schema和测试夹具的要求，但不直接处理它们的创建或管理。相反，它提供了后端必须实现的接口以提供这些资源。

对于每个测试类别（如 `basic`），测试套件定义了需要哪些schema和夹具。您的后端实现负责通过所需接口提供SQL方言特定的schema创建和夹具管理。

-   **Schema 接口**：后端必须实现schema创建接口以处理数据库特定的DDL语句。
-   **夹具 接口**：后端需要根据指定要求提供测试夹具。

### 测试执行流程

1.  **发现**：`pytest` 发现测试（例如，`test_crud.py`）。
2.  **配置加载**：测试套件中的根 `conftest.py` 调用 `load_backend_configs()` 以获取要测试的所有数据库配置列表（包括内置 SQLite 和自定义配置）。
3.  **参数化**：`pytest` 为每个配置创建一个参数化运行。
4.  **Fixture 设置（`database`）**：对于每次运行，`database` fixture 执行以下操作：
    a.  连接到指定的数据库。
    b.  根据测试文件的路径找到正确的 Schema 文件（例如，`basic.sql`）。
    c.  执行 SQL 以创建必要的表。
    d.  返回一个包含已配置的后端实例和连接配置对象的元组。
5.  **模型 Fixture 设置**：像 `user_class` 这样的 fixture 接收来自 `database` fixture 的结果，并将 `fixtures/models.py` 中的通用 `User` 模型绑定到实时数据库连接。
6.  **测试运行**：测试函数（例如，`test_create_user(user_class)`）使用完全配置的模型执行。
7.  **Fixture 拆卸**：`database` fixture 清理数据库（删除表，断开连接）。

### 运行测试

从您的后端项目的根目录，只需运行 `pytest`：

```bash
# 针对所有已配置的后端运行所有测试
pytest

# 只运行基本功能测试
pytest src/rhosocial/activerecord/testsuite/feature/basic/
```

### 生成代码覆盖率报告

此测试套件的目的是测试 `rhosocial-activerecord` 库和其他第三方后端。因此，代码覆盖率应针对这些目标库进行测量。

要生成代码覆盖率报告，您首先需要确保已安装 `pytest-cov`。然后，在运行 `pytest` 时使用 `--cov` 参数指定目标包。

```bash
# 运行测试并为 rhosocial-activerecord 生成 XML 覆盖率报告
pytest --cov=rhosocial.activerecord --cov-report=xml
```

这将在项目根目录中创建一个 `coverage.xml` 文件。您可以检查此文件中的 `<sources>` 和 `<packages>` 标签，以验证报告是为正确的目标库生成的。
