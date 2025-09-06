# RhoSocial ActiveRecord 测试套件文档

## 1. 简介

欢迎使用 RhoSocial ActiveRecord 测试套件。该软件包为所有与 `rhosocial-activerecord` 库集成的数据库后端提供了一套标准化的测试合约。

其主要目标是确保每个后端（无论是官方的还是第三方的）都遵循核心库所期望的一致且正确的行为。

## 2. 核心设计思想

本测试套件遵循“依赖倒置”原则：

- **通用测试逻辑**: `testsuite` 包定义了所有通用的测试用例和 `pytest` 夹具（fixtures）。它不包含任何特定于数据库的实现。
- **后端提供实现**: 具体的后端包（如 `rhosocial-activerecord-mysql`）在开发和测试时，将 `testsuite` 作为开发依赖项。
- **动态注入**: 后端包负责提供特定于其数据库的 **Schema（表结构）**。在运行测试时，`testsuite` 会通过环境变量动态加载并执行这个 Schema，从而将通用测试逻辑应用于特定的数据库实现。

这种设计使得 `testsuite` 保持高度通用和可扩展。

## 3. 如何使用：后端开发者指南

要使用此测试套件来验证您的自定义数据库后端，请遵循以下步骤：

### 步骤 1: 添加为开发依赖

在您的后端项目（例如 `rhosocial-activerecord-mysql`）的 `pyproject.toml` 或 `requirements-dev.txt` 中，将 `rhosocial-activerecord-testsuite` 添加为开发依赖项。

```toml
# pyproject.toml 示例
[project.optional-dependencies]
dev = [
    "rhosocial-activerecord-testsuite>=0.1.0",
    "pytest>=7.0.0"
]
```

### 步骤 2: 创建 Schema 定义文件

在您的后端项目中，创建一个 Python 文件（例如 `tests/schema.py`）。此文件必须包含一个名为 `create_schema` 的函数，该函数接收一个 SQLAlchemy `engine` 对象作为参数。

此函数应使用该 `engine` 来执行 `CREATE TABLE` 语句，为所有测试模型（如 `User`, `Order` 等）创建表结构。

**`tests/schema.py` 示例:**
```python
# /path/to/your/backend/project/tests/schema.py

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

def create_schema(engine):
    """
    使用提供的 engine 创建所有测试所需的数据库表。
    这里的 SQL 语句需要适配您所用的数据库（如 MySQL, PostgreSQL 等）。
    """
    print("Creating schema for the test suite...")
    try:
        with engine.connect() as connection:
            # 删除已存在的表（可选，用于确保测试环境纯净）
            connection.execute(text("DROP TABLE IF EXISTS users;"))
            
            # 创建 users 表
            connection.execute(text("""
                CREATE TABLE users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    age INT,
                    email VARCHAR(255)
                );
            """))
            # 在这里继续创建其他所有测试需要的表...
            
            # 如果是事务性 DDL，需要提交
            if connection.in_transaction():
                connection.commit()
        print("Schema created successfully.")
    except SQLAlchemyError as e:
        print(f"An error occurred while creating the schema: {e}")
        raise

```

### 步骤 3: 运行测试

在您的后端项目根目录下，使用 `pytest` 运行测试。运行时，必须设置以下环境变量：

- **`DB_TYPE`**: 数据库类型，必须与 `rhosocial-activerecord` 中注册的后端名称匹配（例如 `mysql`, `pgsql`, `sqlite`）。
- **`SCHEMA_PATH`**: 指向您在上一步中创建的 schema 文件的 Python 导入路径。例如，如果文件位于 `tests/schema.py`，则路径为 `tests.schema`。
- **数据库连接变量**:
    - `DB_HOST`: 数据库主机
    - `DB_PORT`: 数据库端口
    - `DB_USER`: 用户名
    - `DB_PASSWORD`: 密码
    - `DB_NAME`: 数据库名称

**运行测试的命令行示例:**

```bash
# 设置环境变量并运行 pytest
export DB_TYPE="mysql"
export SCHEMA_PATH="tests.schema"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_USER="root"
export DB_PASSWORD="your_password"
export DB_NAME="test_db"

pytest
```

`pytest` 会自动发现并运行安装在环境中的 `rhosocial-activerecord-testsuite` 包里的所有测试用例，并将它们应用于您配置的数据库和 Schema。

## 4. 生成代码覆盖率报告

为了确保您的后端实现被充分测试，您可以生成覆盖率报告。

```bash
# 运行测试并为您的后端包（例如 my_backend_package）生成覆盖率报告
pytest --cov=my_backend_package --cov-report=html
```

这将在项目根目录下生成一个 `htmlcov/` 目录，您可以在浏览器中打开 `index.html` 查看详细的覆盖率报告。

## 5. 贡献

欢迎为本测试套件做出贡献！请参考主仓库的[贡献指南](https://github.com/rhosocial/python-activerecord/blob/main/CONTRIBUTING.md)。