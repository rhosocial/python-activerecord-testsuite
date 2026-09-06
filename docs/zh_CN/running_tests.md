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

测试套件定义了数据库 schema 和测试夹具的要求，但不直接处理它们的创建或管理。相反，每个主题（topic）都会暴露一个**接口**（`interfaces.py`），后端必须实现该接口以提供这些资源。

对于每个测试主题（如 `basic`），测试套件定义了需要哪些 schema 和夹具。您的后端实现负责通过所需的 provider 接口提供 SQL 方言特定的 schema 创建和夹具管理（`setup_*_fixtures` / `async_setup_*_fixtures` 及其 teardown 配对方法）。

### 测试执行流程

1. **发现**：`pytest` 发现导入到后端自身 `tests/` 树中的测试。
2. **Provider 解析**：测试请求模型夹具（如 `user_class`）；这些夹具通过后端注册的 provider 进行路由，provider 创建 schema 并将模型类配置到实时后端上。
3. **场景参数化**：每个后端通过其 provider 注册一个或多个场景（如 SQLite `memory`、MySQL `mysql_80`）。测试会跨已注册的场景进行参数化；`--scenarios` 选项可选择其中一部分。
4. **测试运行**：`test_create_user(user_class)` 使用绑定到该场景后端的完全配置模型执行。
5. **夹具拆卸**：provider 以正确顺序（数据 → 游标 → 连接）拆卸夹具并断开连接。

## [2. 重要：PYTHONPATH 配置](#2-重要pythonpath-配置)

**运行测试前需设置 `PYTHONPATH`，以便 pytest 能导入后端的测试工具。** 从后端项目根目录运行测试套件时，后端的 `tests/` 目录包含 provider 注册表（如 `tests/providers/registry.py`），测试套件通过 `TESTSUITE_PROVIDER_REGISTRY` 环境变量发现它。没有 `PYTHONPATH=tests`，pytest 无法导入该模块。

### 为什么需要 PYTHONPATH

```
backend-project/
├── src/                    # ← 被测包（如已安装则可导入）
└── tests/
    └── providers/registry.py   # ← 默认不可导入；需要 PYTHONPATH=tests
```

测试套件通过 `TESTSUITE_PROVIDER_REGISTRY`（默认为 `providers.registry:provider_registry`）定位后端的 provider 注册表。没有 `PYTHONPATH=tests`，Python 无法导入 `providers` 包，运行会失败并报 `ImportError: No module named 'providers'`。

### 平台特定命令

**Linux/macOS (bash/zsh):**
```bash
# 单次命令执行（从后端项目根目录）
PYTHONPATH=tests pytest tests/rhosocial/activerecord_test/feature/

# 持续会话
export PYTHONPATH=tests
pytest tests/
```

**Windows (PowerShell):**
```powershell
# 单次命令执行
$env:PYTHONPATH="tests"; pytest tests/

# 持续会话
$env:PYTHONPATH="tests"
pytest tests/
```

**Windows (CMD):**
```cmd
REM 单次命令执行
set PYTHONPATH=tests && pytest tests/

REM 持续会话
set PYTHONPATH=tests
pytest tests/
```

### 没有 PYTHONPATH 的常见错误

```python
# 您会看到的错误（缺少 PYTHONPATH=tests 时）:
ImportError: No module named 'providers'

# 解决方案:
# 运行 pytest 前设置 PYTHONPATH=tests，使后端的
# tests/providers/registry.py 可被导入。
```

### IDE 配置

**PyCharm:**
- 将后端的 `tests/` 标记为 "Sources Root"
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
PYTHONPATH=tests
```

## [3. 运行测试](#3-运行测试)

测试套件由后端包导入运行，而非独立运行。请从后端项目根目录（如 `python-activerecord/`）运行测试，而不要在本目录运行。后端将测试套件接入其自身的 `tests/` 树，并通过其顶层 `tests/conftest.py` 提供 `TESTSUITE_PROVIDER_REGISTRY`。

### 运行导入的测试

```bash
# 运行后端导入的功能测试
pytest tests/rhosocial/activerecord_test/feature/basic

# 运行单个主题（如 relation）
pytest tests/rhosocial/activerecord_test/feature/relation

# 运行整个导入的测试套件
pytest tests/
```

### 同步 / 异步选择

项目配置了 `asyncio_mode = "auto"`，因此 pytest-asyncio 会在收集阶段自动为每个 `async def test_*` 打上 `asyncio` 标记。源码中不写任何显式标记。如需选择：

```bash
# 仅异步测试
pytest tests/ -m asyncio

# 仅同步测试
pytest tests/ -m "not asyncio"

# 或按路径 / 名称（异步文件带有 `_async` 后缀）
pytest tests/ -k async
pytest tests/ -k "not async"
```

### 按类别选择测试

类别通过目录结构表达，而非标记：

```bash
# 功能测试
pytest tests/rhosocial/activerecord_test/feature

# 基准测试
pytest tests/rhosocial/activerecord_test/benchmark
```

### 基于能力的过滤

后端特定能力的跳过由两个通用标记驱动：`requires_protocol` 和 `requires_functions`（详见 `configuration.md`）。可使用以下方式过滤：

```bash
# 列出已注册的标记
pytest --markers

# 仅收集不需要额外能力的测试
pytest tests/ -m "not requires_protocol and not requires_functions" --collect-only
```

## [4. 生成代码覆盖率报告](#4-生成代码覆盖率报告)

此测试套件的目的是测试 `rhosocial-activerecord` 库和其他第三方后端。因此，代码覆盖率应针对这些目标库进行测量。

要生成代码覆盖率报告，您首先需要确保已安装 `pytest-cov`。然后，在运行 `pytest` 时使用 `--cov` 参数指定目标包。

```bash
# 运行测试并为 rhosocial-activerecord 生成 XML 覆盖率报告
pytest --cov=rhosocial.activerecord --cov-report=xml
```

这将在项目根目录中创建一个 `coverage.xml` 文件。您可以检查此文件中的 `<sources>` 和 `<packages>` 标签，以验证报告是为正确的目标库生成的。

## [5. 编写测试](#5-编写测试)

### 对于测试套件作者

**规则:**
- 永远不要导入后端特定的模块
- 永远不要直接编写 SQL（使用 provider 接口）
- 没有声明能力要求时永远不要假定数据库功能
- 始终使用 provider 提供的夹具
- 能力要求只使用两个装饰器：`requires_protocol` 和 `requires_functions`

**示例:**

```python
# 好 - 后端无关且带协议能力声明
from rhosocial.activerecord.backend.dialect.protocols import WindowFunctionSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol, requires_functions

@requires_protocol(WindowFunctionSupport, "supports_window_functions")
def test_window_functions(order_fixtures):
    """测试窗口函数支持。"""
    User, Order, OrderItem = order_fixtures

    user = User(username='test', email='test@example.com')
    assert user.save(), "expected user to be saved"

# 好 - 函数名能力声明
@requires_functions('json_array_insert', 'jsonb_array_insert')
def test_json_insert(json_user_fixtures):
    """测试 JSON 插入函数支持。"""
    pass

# 坏 - 后端特定
def test_basic_cte():
    from rhosocial.activerecord.backend.mysql import MySQLBackend
    # 不要这样做
```

### 对于后端开发者

**规则:**
- 必须实现所有 provider 接口方法（按后端能力，实现 `setup_*_fixtures` 和
  `async_setup_*_fixtures` 配对）。
- 必须创建匹配测试套件结构的 schema 文件。
- 必须通过薄桥文件（`from ...testsuite.feature.<topic>.test_x import *`）
  将测试套件导入到自身的 `tests/` 树中。
- 必须处理数据库连接池并清理测试数据。
- 必须从 provider 方法返回元组（即使对于单个模型）。
- 能力处理由方言驱动：`requires_protocol` 读取 Protocol 类支持，
  `requires_functions` 读取 `supports_functions(...)` — 后端不再用 `add_*`
  方法单独声明能力。