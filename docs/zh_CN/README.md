# RhoSocial ActiveRecord 测试套件文档

## 1. 简介

欢迎使用 RhoSocial ActiveRecord 测试套件。该软件包为所有与 `rhosocial-activerecord` 库集成的数据库后端提供了一套标准化的测试合约。

其主要目标是确保每个后端（无论是官方的还是第三方的）都遵循核心库所期望的一致且正确的行为。该套件建立在三大支柱之上：

-   **功能测试 (Feature Tests)**: 验证独立、原子化的功能（例如 CRUD 操作、查询方法、字段类型）。
-   **真实世界场景 (Real-world Scenarios)**: 模拟复杂的业务逻辑，以测试不同组件之间的交互。
-   **性能基准测试 (Benchmark Tests)**: 衡量和比较不同后端的性能指标。

## 2. 后端开发者入门指南

要使用此测试套件来验证您的自定义数据库后端，请遵循以下步骤：

### 先决条件

-   一个可工作的、继承自 `rhosocial.activerecord.backend.StorageBackend` 的数据库后端实现。
-   您的后端包应该可以在测试环境中被安装。

### 安装

在您的后端项目的 `pyproject.toml` 中，将 `rhosocial-activerecord-testsuite` 添加为开发依赖项：

```toml
[project.optional-dependencies]
dev = [
    "rhosocial-activerecord-testsuite>=0.1.0"
]
```

## 3. 配置

本测试套件由一个灵活的配置系统驱动，允许您针对多个数据库版本和设置进行测试。

### 后端驱动与命名空间

在配置之前，理解后端是如何被加载的非常重要：

-   **官方后端**: 由 `rhosocial` 发布的后端被安装在 `rhosocial.activerecord.backend.impl` 命名空间下（例如 `...impl.mysql`）。测试套件的默认配置加载器知道如何找到它们。
-   **第三方后端**: 如果您正在开发第三方后端，它应该位于自己的命名空间下（例如 `acme_corp.activerecord.backend.impl.acme_db`）。为了让测试套件能够识别您的驱动，您需要注册它，通常是在您包的 `pyproject.toml` 中使用 Python 的 `entry_points` 机制。在 `backends.yml` 中，`driver` 键的值将对应您注册的驱动名称。

### 内置 SQLite 支持

本测试套件内置了对 `rhosocial-activerecord` 自带的 `sqlite` 后端的测试支持。具体使用哪个配置取决于您用来运行测试的 Python 版本。

-   **自动检测**: 默认情况下，测试套件会检测当前的 Python 版本（例如 3.11），并针对其对应的 SQLite 版本运行测试（例如 `sqlite_py311_mem` 和 `sqlite_py311_file`）。
-   **CI/CD 覆盖**: 您可以通过设置 `PYTEST_TARGET_VERSION` 环境变量来强制测试针对特定 Python 版本的配置运行。例如：
    ```bash
    PYTEST_TARGET_VERSION=3.10 pytest
    ```

### 自定义后端配置 (`backends.yml`)

要测试您自己的后端（或其他可选后端，如 MySQL、PostgreSQL），您需要在项目的根目录下创建一个 `backends.yml` 文件。

**MySQL 后端的 `backends.yml` 示例：**
```yaml
mysql:
  # 此配置的自定义名称
  mysql_8_0:
    # 驱动名称必须与一个已注册的后端驱动匹配
    driver: mysql 
    host: "127.0.0.1"
    port: 3306
    username: "root"
    password: "password"
    database: "testsuite_db"
```
测试运行器将自动发现并使用此文件，以针对您配置的 MySQL 实例运行完整的测试套件。

## 4. 运行功能测试

本节详细说明如何运行 `feature` 测试。`basic` 目录下的测试覆盖了 ActiveRecord 的基础功能, 包括:

-   **CRUD 操作**: 创建、读取、更新和删除记录 (`test_crud.py`)。
-   **字段类型处理**: 对各种数据类型 (字符串、数字、布尔、日期时间、JSON等) 的正确性验证 (`test_fields.py`)。
-   **数据验证**: 包括基于 Pydantic 的字段级验证和自定义的业务规则验证 (`test_validation.py`)。

### Schema 定义

测试套件对数据库 schema（表结构）采用“约定优于配置”的方式。对于每个测试类别（如 `basic`），您必须在相应的 `schemas` 目录中提供一个 schema 文件。您后端的测试运行器需要提供适用于其 SQL 方言的该文件版本。

-   **示例路径**: `.../testsuite/feature/basic/schemas/basic.sql`
-   **内容**: 此文件应包含 `.../feature/basic/` 目录中测试所需的所有 `CREATE TABLE` 语句。

### 测试执行流程

1.  **发现**: `pytest` 发现测试文件（例如 `test_crud.py`）。
2.  **加载配置**: 测试套件的根 `conftest.py` 调用 `load_backend_configs()` 来获取所有要测试的数据库配置列表（包括内置的 SQLite 和来自 `backends.yml` 的自定义配置）。
3.  **参数化**: `pytest` 为每个配置创建一个参数化的测试运行实例。
4.  **夹具设置 (`database`)**: 对于每次运行, `database` 夹具会执行以下操作：
    a.  连接到指定的数据库。
    b.  根据测试文件的路径找到正确的 schema 文件（例如 `basic.sql`）。
    c.  执行 SQL 以创建必要的表。
    d.  向测试函数 `yield` 一个配置好的后端实例和连接配置对象的元组。
5.  **模型夹具设置**: 像 `user_class` 这样的夹具会接收 `database` 夹具的结果, 并将 `fixtures/models.py` 中的通用 `User` 模型与活动的数据库连接进行绑定。
6.  **运行测试**: 测试函数（例如 `test_create_user(user_class)`）使用完全配置好的模型来执行。
7.  **夹具拆卸**: `database` 夹具清理数据库状态（删除表, 断开连接）。

### 运行测试

在您的后端项目的根目录中，只需运行 `pytest`：

```bash
# 针对所有已配置的后端运行所有测试
pytest

# 仅运行基础功能测试
pytest src/rhosocial/activerecord/testsuite/feature/basic/
```

## 5. 代码规范

为了保持代码库的清晰和一致性, 我们约定:

- **路径注释**: 所有位于 `src/` 目录下的文件 (包括 `.py`, `.sql` 等), 都必须在文件的第一行添加一个注释, 内容为该文件相对于项目根目录 (`python-activerecord-testsuite`) 的相对路径。

  例如: `# src/rhosocial/activerecord/testsuite/conftest.py`

## 6. 常见问题

在运行和调试测试套件时, 可能会遇到各种环境和代码问题。我们整理了一份详细的指南来帮助您解决这些问题。

-   [常见问题与调试指南](./TROUBLESHOOTING.md)

## 7. 贡献

欢迎为本测试套件做出贡献！请参考主仓库的[贡献指南](https://github.com/rhosocial/python-activerecord/blob/main/CONTRIBUTING.md)。
