# 运行测试

本指南解释了如何使用测试套件执行测试。

## 目录
- [1. 运行功能测试](#1-运行功能测试)
- [2. 重要：PYTHONPATH 配置](#2-重要pythonpath-配置)
- [3. 运行测试](#3-运行测试)
- [4. 生成代码覆盖率报告](#4-生成代码覆盖率报告)
- [5. 编写测试](#5-编写测试)

## [1. 运行功能测试](#1-运行功能测试)

本节详细介绍了如何运行 `feature` 测试。`basic` 目录下的测试涵盖了 ActiveRecord 的基本功能，包括：

- **CRUD 操作**：创建、读取、更新和删除记录（`test_crud.py`）。
- **字段类型处理**：验证各种数据类型（字符串、数字、布尔值、日期时间、JSON 等）（`test_fields.py`）。
- **数据验证**：包括通过 Pydantic 进行的字段级验证和自定义业务规则验证（`test_validation.py`）。

### Schema 定义和夹具

测试套件定义了数据库schema和测试夹具的要求，但不直接处理它们的创建或管理。相反，它提供了**接口**，后端必须实现这些接口以提供这些资源。

对于每个测试类别（如 `basic`），测试套件定义了需要哪些schema和夹具。您的后端实现负责通过所需接口提供SQL方言特定的schema创建和夹具管理。

- **Schema 接口**：后端必须实现schema创建接口以处理数据库特定的DDL语句。
- **夹具 接口**：后端需要根据指定要求提供测试夹具。

### 测试执行流程

1. **发现**：`pytest` 发现测试（例如，`test_crud.py`）。
2. **配置加载**：测试套件中的根 `conftest.py` 调用 `load_backend_configs()` 以获取要测试的所有数据库配置列表（包括内置 SQLite 和自定义配置）。
3. **参数化**：`pytest` 为每个配置创建一个参数化运行。
4. **Fixture 设置（`database`）**：对于每次运行，`database` fixture 执行以下操作：
    a. 连接到指定的数据库。
    b. 根据测试文件的路径找到正确的 Schema 文件（例如，`basic.sql`）。
    c. 执行 SQL 以创建必要的表。
    d. 返回一个包含已配置的后端实例和连接配置对象的元组。
5. **模型 Fixture 设置**：像 `user_class` 这样的 fixture 接收来自 `database` fixture 的结果，并将 `fixtures/models.py` 中的通用 `User` 模型绑定到实时数据库连接。
6. **测试运行**：测试函数（例如，`test_create_user(user_class)`）使用完全配置的模型执行。
7. **Fixture 拆卸**：`database` fixture 清理数据库（删除表，断开连接）。

## 2. 重要：PYTHONPATH 配置

**必须在运行测试前配置 PYTHONPATH。** 测试目录（`tests/`, `tests_original/`）**不在** Python 路径中。

### 为什么需要 PYTHONPATH

```
项目根目录/
├── src/rhosocial/activerecord/    # ← Python 可以导入此目录
├── tests/                          # ← 默认不可导入
└── tests_original/                 # ← 默认不可导入
```

测试从 `rhosocial.activerecord` 导入，但测试文件本身不在包结构中。没有 PYTHONPATH，pytest 无法找到源代码。

### 平台特定命令

**Linux/macOS (bash/zsh):**
```bash
# 单次命令执行
PYTHONPATH=src pytest tests/

# 持续会话
export PYTHONPATH=src
pytest tests/
```

**Windows (PowerShell):**
```powershell
# 单次命令执行
$env:PYTHONPATH="src"; pytest tests/

# 持续会话
$env:PYTHONPATH="src"
pytest tests/
```

**Windows (CMD):**
```cmd
REM 单次命令执行
set PYTHONPATH=src && pytest tests/

REM 持续会话
set PYTHONPATH=src
pytest tests/
```

### 没有 PYTHONPATH 的常见错误

```python
# 您会看到的错误:
ModuleNotFoundError: No module named 'rhosocial.activerecord'

# 解决方案:
# 在运行 pytest 之前设置 PYTHONPATH=src
```

### IDE 配置

**PyCharm:**
- 将 `src/` 标记为 "Sources Root"
- 测试运行器自动将其添加到 PYTHONPATH

**VS Code:**
```json
// .vscode/settings.json
{
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.pytestEnabled": true,
    "python.envFile": "${workspaceFolder}/.env"
}
```

```bash
# .env 文件
PYTHONPATH=src
```

## 3. 运行测试

### 快速参考

```bash
# 始终先设置 PYTHONPATH
export PYTHONPATH=src  # 或适用于您平台的等效命令

# 针对所有已配置的后端运行所有测试
pytest tests/

# 运行测试套件验证测试
pytest tests/ --run-testsuite

# 运行特定功能测试
pytest tests/ --run-testsuite -m "feature_crud"

# 运行原始综合测试
pytest tests_original/

# 以能力报告运行
pytest tests/ --run-testsuite --show-skipped-capabilities
```

### 按标记选择测试

```bash
# 功能测试
pytest -m "feature"
pytest -m "feature_crud"
pytest -m "feature_query"

# 真实场景
pytest -m "realworld"
pytest -m "scenario_ecommerce"

# 基准
pytest -m "benchmark"
pytest -m "benchmark_bulk"
```

## 4. 生成代码覆盖率报告

此测试套件的目的是测试 `rhosocial-activerecord` 库和其他第三方后端。因此，代码覆盖率应针对这些目标库进行测量。

要生成代码覆盖率报告，您首先需要确保已安装 `pytest-cov`。然后，在运行 `pytest` 时使用 `--cov` 参数指定目标包。

```bash
# 运行测试并为 rhosocial-activerecord 生成 XML 覆盖率报告
pytest --cov=rhosocial.activerecord --cov-report=xml
```

这将在项目根目录中创建一个 `coverage.xml` 文件。您可以检查此文件中的 `<sources>` 和 `<packages>` 标签，以验证报告是为正确的目标库生成的。

## 5. 编写测试

### 对于测试套件作者

**规则:**
- 永远不要导入后端特定的模块
- 永远不要直接编写SQL（使用提供者接口）
- 没有声明能力要求时永远不要假定数据库功能
- 始终使用提供者提供的夹具
- 始终使用 pytest 标记
- 始终在要求中指定类别和特定能力

**示例:**

```python
# 好 - 后端无关且带能力声明
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    CTECapability
)
from rhosocial.activerecord.testsuite.utils import requires_capabilities

@pytest.mark.feature
@pytest.mark.feature_query
@requires_capabilities((CapabilityCategory.CTE, CTECapability.BASIC_CTE))
def test_basic_cte(order_fixtures):
    """测试基本CTE功能。"""
    User, Order, OrderItem = order_fixtures
    
    user = User(username='test', email='test@example.com')
    assert user.save()

# 坏 - 在能力要求中缺少类别
@requires_capabilities(CTECapability.BASIC_CTE)  # 错误 - 没有类别
def test_basic_cte(order_fixtures):
    pass

# 坏 - 后端特定
def test_basic_cte():
    from rhosocial.activerecord.backend.mysql import MySQLBackend
    # 不要这样做
```

### 对于后端开发者

**规则:**
- 必须实现所有提供者接口方法
- 必须创建匹配测试套件结构的schema文件
- 必须将后端特定测试前缀为 `test_{backend}_`
- 必须处理数据库连接池
- 必须清理测试数据
- 必须使用 add_* 方法准确声明后端能力
- 必须从提供者方法返回元组（即使对于单个模型）