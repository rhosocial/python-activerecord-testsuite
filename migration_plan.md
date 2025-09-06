# 测试套件迁移规划（修订版）

## 包名和路径关系说明

### 包名与仓库路径对应关系
本项目采用分布式包架构，包名与仓库路径需要区分：

| 包名 | 仓库路径 | 用途 |
|------|----------|------|
| `rhosocial-activerecord` | `rhosocial/python-activerecord` | 核心包（包含SQLite后端） |
| `rhosocial-activerecord-mysql` | `rhosocial/python-activerecord-mysql` | MySQL后端扩展包 |
| `rhosocial-activerecord-postgresql` | `rhosocial/python-activerecord-postgresql` | PostgreSQL后端扩展包 |
| `rhosocial-activerecord-testsuite` | `rhosocial/python-activerecord-testsuite` | 独立测试套件包 |

**重要说明**：
- **包名**：用于 `pip install` 和 `import` 的标识符
- **仓库路径**：GitHub组织下的实际仓库路径
- 所有包共享 `rhosocial.activerecord` 命名空间，通过 `pkgutil.extend_path` 实现

## testsuite功能概述

### testsuite的核心作用
`rhosocial-activerecord-testsuite` 是一个独立的测试套件包，为所有ActiveRecord后端实现提供标准化的测试用例和验证机制。

### 目录结构和功能划分

#### 1. feature/ - 核心功能测试（必须运行）
```
feature/
├── basic/              # 基础CRUD功能测试
│   ├── test_crud.py   # 创建、读取、更新、删除操作
│   ├── test_fields.py # 字段类型处理和转换
│   └── test_validation.py # 数据验证机制
├── relations/          # 关系功能测试（举例，下同）  
│   ├── test_has_many.py    # 一对多关系
│   ├── test_belongs_to.py  # 多对一关系
│   └── test_many_to_many.py # 多对多关系
└── query/              # 查询功能测试（举例，下同）
    ├── test_where.py   # 条件查询
    ├── test_joins.py   # 表连接
    └── test_aggregates.py # 聚合查询
```

**功能说明**：feature目录包含所有后端必须通过的核心功能测试，确保ActiveRecord的基本约定和接口一致性。

#### 2. realworld/ - 真实场景测试（可选运行）
```
realworld/
├── test_blog_system.py     # 博客系统场景（举例，下同）
├── test_user_management.py # 用户管理场景
├── test_ecommerce.py       # 电商系统场景
└── test_social_network.py  # 社交网络场景
```

**功能说明**：realworld目录模拟真实业务场景，测试复杂的业务逻辑组合，验证在实际应用中的表现。

#### 3. benchmark/ - 性能基准测试（可选运行）
```
benchmark/
├── test_crud_performance.py    # CRUD操作性能（举例，下同）
├── test_query_performance.py   # 查询性能
├── test_bulk_operations.py     # 批量操作性能
└── test_concurrent_access.py   # 并发访问性能
```

**功能说明**：benchmark目录提供性能基准测试，帮助评估不同后端的性能特性和优化效果。

### testsuite的价值
- **标准化**：确保所有后端实现遵循相同的接口约定
- **质量保证**：通过统一测试用例验证功能正确性
- **性能对比**：提供性能基准，便于选择合适的后端
- **开发效率**：后端开发者专注实现，无需重复编写测试

## 一、架构设计原则

### 1.1 核心原则
- **责任分离**: testsuite 只提供测试用例和夹具接口定义，后端负责所有环境准备和资源管理
- **约定优于配置**: 通过目录结构约定减少配置复杂度
- **最小化依赖**: testsuite 保持轻量，只依赖必要的测试框架
- **渐进式迁移**: 支持增量迁移，降低迁移风险
- **便捷集成**: 后端包执行 `pytest` 即可运行完整测试套件

### 1.2 责任边界
**testsuite 负责**:
- 定义测试用例
- 定义夹具接口（IProvider）
- 实现夹具调度逻辑
- 提供测试文档

**后端实现负责**:
- 实现夹具接口
- 管理数据库schema
- 处理资源隔离
- 优化性能

## 二、目录结构设计

### 2.1 testsuite 包结构
```
rhosocial-activerecord-testsuite/    # 包名
# 仓库路径：rhosocial/python-activerecord-testsuite
├── pyproject.toml
├── README.md
├── src/
│   └── rhosocial/
│       └── activerecord/
│           └── testsuite/
│               ├── __init__.py
│               ├── conftest.py              # 全局夹具和provider注册
│               ├── core/                    # 核心工具
│               │   ├── __init__.py
│               │   ├── registry.py          # Provider注册表接口
│               │   ├── discovery.py         # 接口发现机制
│               │   └── markers.py           # pytest标记定义
│               ├── feature/                 # 功能测试（必须）
│               │   ├── __init__.py
│               │   ├── basic/              # 基础CRUD测试
│               │   │   ├── __init__.py
│               │   │   ├── conftest.py     # basic夹具组
│               │   │   ├── interfaces.py   # IBasicProvider接口
│               │   │   ├── fixtures/       # 模型定义和数据
│               │   │   │   ├── __init__.py
│               │   │   │   └── models.py   # 测试模型定义
│               │   │   ├── test_crud.py
│               │   │   ├── test_fields.py
│               │   │   └── test_validation.py
│               │   ├── relations/          # 关系测试
│               │   │   ├── __init__.py
│               │   │   ├── conftest.py
│               │   │   ├── interfaces.py   # IRelationsProvider接口
│               │   │   ├── fixtures/
│               │   │   │   └── models.py   # 关系模型定义
│               │   │   └── test_*.py
│               │   └── query/              # 查询测试
│               │       ├── __init__.py
│               │       ├── conftest.py
│               │       ├── interfaces.py   # IQueryProvider接口
│               │       ├── fixtures/
│               │       │   └── models.py   # 查询模型定义
│               │       └── test_*.py
│               ├── realworld/               # 真实场景测试（可选）
│               │   ├── __init__.py
│               │   ├── conftest.py
│               │   ├── interfaces.py
│               │   ├── fixtures/
│               │   │   └── models.py       # 业务场景模型
│               │   └── test_*.py
│               └── benchmark/               # 性能测试（可选）
│                   ├── __init__.py
│                   ├── conftest.py
│                   ├── interfaces.py
│                   ├── fixtures/
│                   │   └── models.py       # 性能测试模型
│                   └── test_*.py
```

### 2.2 后端实现结构（以 rhosocial-activerecord 为例）
```
rhosocial-activerecord/                     # 包名
# 仓库路径：rhosocial/python-activerecord
├── src/
│   └── rhosocial/
│       └── activerecord/
│           └── ... (现有代码)
├── pytest.ini                             # pytest配置
├── pyproject.toml                          # 项目配置（包含测试配置）
└── tests/                                  # 测试目录
    ├── __init__.py
    ├── conftest.py                         # pytest配置和Provider注册
    ├── providers/                          # Provider实现
    │   ├── __init__.py
    │   ├── registry.py                     # Provider注册表实现
    │   ├── scenarios.py                    # 场景配置映射表
    │   ├── basic.py                        # BasicProvider实现
    │   ├── relations.py                    # RelationsProvider实现
    │   ├── query.py                        # QueryProvider实现
    │   ├── realworld.py                    # RealworldProvider实现（可选）
    │   └── benchmark.py                    # BenchmarkProvider实现（可选）
    ├── fixtures/                           # 测试夹具数据
    │   ├── schemas/                        # SQL schema文件
    │   │   └── sqlite/                     # SQLite专用schema
    │   │       ├── type_cases.sql
    │   │       ├── type_tests.sql
    │   │       ├── users.sql
    │   │       ├── validated_field_users.sql
    │   │       └── validated_users.sql
    │   └── data/                           # 测试数据文件
    │       ├── sample_users.json
    │       └── sample_posts.json
    ├── integration/                        # 后端特定的集成测试
    │   ├── __init__.py
    │   ├── test_sqlite_specific.py
    │   └── test_performance.py
    └── rhosocial/
        └── activerecord_test/
            ├── __init__.py
            ├── feature/                    # 核心功能测试
            │   ├── __init__.py
            │   ├── basic/                  # 基础CRUD功能测试
            │   │   ├── __init__.py
            │   │   ├── test_crud.py
            │   │   ├── test_fields.py
            │   │   └── test_validation.py
            │   ├── relations/              # 关系功能测试
            │   │   ├── __init__.py
            │   │   ├── test_has_many.py
            │   │   ├── test_belongs_to.py
            │   │   └── test_many_to_many.py
            │   └── query/                  # 查询功能测试
            │       ├── __init__.py
            │       ├── test_where.py
            │       ├── test_joins.py
            │       └── test_aggregates.py
            ├── realworld/                  # 真实场景测试（可选）
            │   ├── __init__.py
            │   ├── test_blog_system.py
            │   ├── test_user_management.py
            │   └── test_ecommerce.py
            └── benchmark/                  # 性能基准测试（可选）
                ├── __init__.py
                ├── test_crud_performance.py
                ├── test_query_performance.py
                └── test_bulk_operations.py
```

## 三、简化的场景配置机制（修订版）

### 3.1 核心设计原则

#### 后端专注性原则
- **单一后端关注**：每个后端包只关心自己的配置和测试场景
- **无跨后端依赖**：不检查或配置其他后端类型
- **独立维护**：各后端包独立维护自己的场景配置

#### 责任分离原则
- **testsuite负责**：模型定义、测试逻辑、夹具接口
- **后端负责**：场景配置、schema管理、Provider实现
- **清晰边界**：testsuite不涉及具体数据库操作，后端不定义业务模型

### 3.2 SQLite后端场景配置（rhosocial-activerecord示例）

#### 场景映射表设计
```python
# tests/providers/scenarios.py
"""SQLite后端的简化测试场景配置映射表"""

import os
import tempfile
from typing import Dict, Any, Tuple, Type
from rhosocial.activerecord.backend.impl.sqlite.backend import SQLiteBackend
from rhosocial.activerecord.backend.impl.sqlite.config import SQLiteConnectionConfig

# 场景名 -> 配置字典 的映射表（只关心SQLite）
SCENARIO_MAP: Dict[str, Dict[str, Any]] = {}

def register_scenario(name: str, config: Dict[str, Any]):
    """注册SQLite测试场景"""
    SCENARIO_MAP[name] = config

def get_scenario(name: str) -> Tuple[Type[SQLiteBackend], SQLiteConnectionConfig]:
    """
    Retrieves the backend class and a connection configuration object for a given
    scenario name. This is called by the provider to set up the database for a test.
    """
    if name not in SCENARIO_MAP:
        name = "memory"  # Fallback to the default in-memory scenario if not found.
    
    # Unpack the configuration dictionary into the dataclass constructor.
    config = SQLiteConnectionConfig(**SCENARIO_MAP[name])
    return SQLiteBackend, config

def get_enabled_scenarios() -> Dict[str, Any]:
    """
    Returns the map of all currently enabled scenarios. The testsuite's conftest
    uses this to parameterize the tests, causing them to run for each scenario.
    """
    return SCENARIO_MAP

def _register_default_scenarios():
    """
    Registers the default scenarios supported by this SQLite backend.
    More complex scenarios (e.g., for performance or concurrency testing)
    can be added here, often controlled by environment variables.
    """
    # The default, fastest scenario using an in-memory SQLite database.
    register_scenario("memory", {
        "database": ":memory:",
    })
    
    # 临时文件数据库（持久化测试）
    if os.getenv("TEST_SQLITE_FILE", "false").lower() == "true":
        temp_dir = tempfile.gettempdir()
        register_scenario("tempfile", {
            "database": os.path.join(temp_dir, "test_activerecord.sqlite"),
            "delete_on_close": True
        })
    
    # 调试模式（显示SQL语句）。注意：'echo' 和 'auto_commit' 不是 SQLiteConnectionConfig 的参数。
    # 要启用 SQL 回显，请配置 'rhosocial.activerecord' 的日志级别。
    if os.getenv("TEST_SQLITE_DEBUG", "false").lower() == "true":
        register_scenario("debug", {
            "database": ":memory:",
        })
    
    # 性能测试模式（优化设置）。注意：'echo' 不是 SQLiteConnectionConfig 的参数。
    if os.getenv("TEST_SQLITE_PERFORMANCE", "false").lower() == "true":
        register_scenario("performance", {
            "database": ":memory:",
            "pragmas": {
                "synchronous": "OFF",
                "journal_mode": "MEMORY",
                "temp_store": "MEMORY",
                "cache_size": 10000
            }
        })
    
    # 并发测试模式（WAL模式）。注意：'echo' 和 'auto_commit' 是不是 SQLiteConnectionConfig 的参数。
    if os.getenv("TEST_SQLITE_CONCURRENT", "false").lower() == "true":
        register_scenario("concurrent", {
            "database": "test_concurrent.sqlite",
            "delete_on_close": True,
            "pragmas": {
                "journal_mode": "WAL",
                "synchronous": "NORMAL"
            }
        })

# 初始化时注册默认场景
_register_default_scenarios()
```

#### 环境变量配置
```bash
# SQLite后端专用环境变量
export TEST_SQLITE_FILE=true          # 启用文件数据库测试
export TEST_SQLITE_DEBUG=true         # 启用调试模式
export TEST_SQLITE_PERFORMANCE=true   # 启用性能测试
export TEST_SQLITE_CONCURRENT=true    # 启用并发测试

# 场景选择
export ENABLED_TEST_SCENARIOS="memory,debug"  # 只运行指定场景
```

### 3.3 Provider实现（SQLite后端）

#### BasicProvider实现
```python
# tests/providers/basic.py
"""
This file provides the concrete implementation of the `IBasicProvider` interface
that is defined in the `rhosocial-activerecord-testsuite` package.

Its main responsibilities are:
1.  Reporting which test scenarios (database configurations) are available.
2.  Setting up the database environment for a given test. This includes:
    - Getting the correct database configuration for the scenario.
    - Configuring the ActiveRecord model with a database connection.
    - Dropping any old tables and creating the necessary table schema.
3.  Cleaning up any resources (like temporary database files) after a test runs.
"""
import os
from typing import Type, List
from rhosocial.activerecord import ActiveRecord
from rhosocial.activerecord.testsuite.feature.basic.interfaces import IBasicProvider
# The models are defined generically in the testsuite...
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import User, TypeCase, ValidatedFieldUser, TypeTestModel, ValidatedUser
# ...and the scenarios are defined specifically for this backend.
from .scenarios import get_enabled_scenarios, get_scenario

class BasicProvider(IBasicProvider):
    """
    This is the SQLite backend's implementation for the basic features test group.
    It connects the generic tests in the testsuite with the actual SQLite database.
    """

    def get_test_scenarios(self) -> List[str]:
        """Returns a list of names for all enabled scenarios for this backend."""
        return list(get_enabled_scenarios().keys())

    def _setup_model(self, model_class: Type[ActiveRecord], scenario_name: str, table_name: str) -> Type[ActiveRecord]:
        """A generic helper method to handle the setup for any given model."""
        # 1. Get the backend class (SQLiteBackend) and connection config for the requested scenario.
        backend_class, config = get_scenario(scenario_name)
        
        # 2. Configure the generic model class with our specific backend and config.
        #    This is the key step that links the testsuite's model to our database.
        model_class.configure(config, backend_class)
        
        # 3. Prepare the database schema. To ensure tests are isolated, we drop
        #    the table if it exists and recreate it from the schema file.
        try:
            model_class.__backend__.execute(f"DROP TABLE IF EXISTS {table_name}")
        except Exception:
            # Ignore errors if the table doesn't exist, which is expected on the first run.
            pass
            
        schema_sql = self._load_sqlite_schema(f"{table_name}.sql")
        model_class.__backend__.execute(schema_sql)
        
        return model_class

    # --- Implementation of the IBasicProvider interface ---

    def setup_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Sets up the database for the `User` model tests."""
        return self._setup_model(User, scenario_name, "users")

    def setup_type_case_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Sets up the database for the `TypeCase` model tests."""
        return self._setup_model(TypeCase, scenario_name, "type_cases")

    def setup_type_test_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Sets up the database for the `TypeTestModel` model tests."""
        return self._setup_model(TypeTestModel, scenario_name, "type_tests")

    def setup_validated_field_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Sets up the database for the `ValidatedFieldUser` model tests."""
        return self._setup_model(ValidatedFieldUser, scenario_name, "validated_field_users")

    def setup_validated_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Sets up the database for the `ValidatedUser` model tests."""
        return self._setup_model(ValidatedUser, scenario_name, "validated_users")

    def _load_sqlite_schema(self, filename: str) -> str:
        """Helper to load a SQL schema file from this project's fixtures."""
        # Schemas are stored locally within this backend's test directory.
        schema_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures", "schemas", "sqlite")
        schema_path = os.path.join(schema_dir, filename)
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            return f.read()

    def cleanup_after_test(self, scenario_name: str):
        """
        Performs cleanup after a test. For file-based scenarios, this involves
        deleting the temporary database file.
        """
        _, config = get_scenario(scenario_name)
        if config.delete_on_close and config.database != ":memory:" and os.path.exists(config.database):
            try:
                # Attempt to remove the temp db file.
                os.remove(config.database)
            except OSError:
                # Ignore errors if the file is already gone or locked, etc.
                pass
```

### 3.4 MySQL后端的场景配置示例

```python
# rhosocial-activerecord-mysql/tests/providers/scenarios.py  
# 仓库路径：rhosocial/python-activerecord-mysql
"""MySQL后端的测试场景配置映射表"""

import os
from typing import Dict, Any, Tuple, Type
from rhosocial.activerecord.backend.impl.mysql import MySQLBackend
from rhosocial.activerecord.backend.impl.mysql.config import MySQLConnectionConfig

# MySQL专用场景配置
SCENARIO_MAP: Dict[str, Dict[str, Any]] = {}

def register_scenario(name: str, config: Dict[str, Any]):
    """注册MySQL测试场景"""
    SCENARIO_MAP[name] = config

def get_scenario(name: str) -> Tuple[Type[MySQLBackend], Dict[str, Any]]:
    """获取MySQL测试场景"""
    if name not in SCENARIO_MAP:
        raise ValueError(f"未找到MySQL测试场景: {name}")
    return MySQLBackend, SCENARIO_MAP[name]

def _register_default_scenarios():
    """注册默认的MySQL测试场景"""
    
    # 本地开发环境
    register_scenario("local", {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "test_activerecord"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "charset": "utf8mb4",
        "autocommit": True
    })
    
    # Docker测试环境
    if os.getenv("TEST_MYSQL_DOCKER", "false").lower() == "true":
        register_scenario("docker", {
            "host": "127.0.0.1",
            "port": 3307,  # 映射到不同端口避免冲突
            "database": "test_db",
            "user": "testuser",
            "password": "testpass",
            "charset": "utf8mb4"
        })
    
    # 性能测试环境
    if os.getenv("TEST_MYSQL_PERFORMANCE", "false").lower() == "true":
        register_scenario("performance", {
            "host": os.getenv("MYSQL_PERF_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PERF_PORT", "3306")),
            "database": "perf_test_db",
            "user": os.getenv("MYSQL_PERF_USER", "root"),
            "password": os.getenv("MYSQL_PERF_PASSWORD", ""),
            "charset": "utf8mb4",
            "pool_size": 20,  # 连接池优化
            "max_overflow": 30
        })

_register_default_scenarios()
```

### 3.5 Provider使用场景配置的统一模式

#### 通用Provider模板
```python
# 适用于所有后端的Provider实现模式
class BackendProvider:
    """通用后端Provider实现模式"""
    
    def setup_model(self, model_name: str, test_name: str, scenario_name: str = "default"):
        """通用模型设置模式"""
        
        # 1. 获取当前后端的场景配置
        backend_class, config_dict = get_scenario(scenario_name)
        
        # 2. 从testsuite获取模型定义（不在后端中定义）
        ModelClass = self._get_model_from_testsuite(model_name)
        
        # 3. 配置当前后端
        config = self._create_connection_config(config_dict)
        ModelClass.configure(config, backend_class)
        
        # 4. 准备当前后端的schema
        self._setup_backend_schema(ModelClass, model_name)
        
        return ModelClass
    
    def _get_model_from_testsuite(self, model_name: str) -> Type[ActiveRecord]:
        """从testsuite获取模型定义（必须实现）"""
        raise NotImplementedError("子类必须实现从testsuite获取模型的方法")
    
    def _create_connection_config(self, config_dict: Dict[str, Any]):
        """创建当前后端的连接配置（必须实现）"""
        raise NotImplementedError("子类必须实现连接配置创建方法")
    
    def _setup_backend_schema(self, model_class: Type[ActiveRecord], table_name: str):
        """设置当前后端的表结构（必须实现）"""
        raise NotImplementedError("子类必须实现schema设置方法")
```

### 3.6 关键设计要点

#### 后端专注性
- **只关心自己**：每个后端包的scenarios.py只配置自己的场景
- **无交叉依赖**：不检查其他后端是否可用
- **简化维护**：减少复杂度，专注核心功能

#### 模型来源统一
- **testsuite提供**：所有业务模型定义都在testsuite中
- **后端获取**：通过导入语句从testsuite获取模型类
- **schema分离**：后端只负责数据库schema，不定义Python模型

#### 场景命名规范
- **后端无关**：场景名不包含后端类型前缀
- **功能导向**：按用途命名（memory, debug, performance）
- **环境友好**：通过环境变量控制场景启用

#### 配置优先级
```bash
# 环境变量控制场景启用
TEST_BACKEND_DEBUG=true      # 启用调试场景
TEST_BACKEND_PERFORMANCE=true  # 启用性能场景

# 运行时选择场景
ENABLED_TEST_SCENARIOS="memory,debug" pytest

# 或者通过命令行参数
pytest --test-scenarios="performance"
```

## 四、直接导入测试方案

### 4.1 测试集成文件（简洁版）
```python
# tests/rhosocial/activerecord_test/feature/basic/test_crud.py
"""
基础CRUD功能测试

直接导入并运行testsuite的基础CRUD测试。
"""

# 设置环境变量（如果还没设置）
import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

# 确保Provider已注册
from tests.providers.registry import provider_registry

# 直接导入testsuite测试，pytest会自动发现
from rhosocial.activerecord.testsuite.feature.basic.test_crud import *

# tests/rhosocial/activerecord_test/feature/basic/test_fields.py
"""
字段类型处理和转换测试

直接导入并运行testsuite的字段类型测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.basic.test_fields import *

# tests/rhosocial/activerecord_test/feature/basic/test_validation.py
"""
数据验证机制测试

直接导入并运行testsuite的数据验证测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.basic.test_validation import *

# tests/rhosocial/activerecord_test/feature/relations/test_has_many.py
"""
一对多关系测试

直接导入并运行testsuite的一对多关系测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.relations.test_has_many import *

# tests/rhosocial/activerecord_test/feature/relations/test_belongs_to.py
"""
多对一关系测试

直接导入并运行testsuite的多对一关系测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.relations.test_belongs_to import *

# tests/rhosocial/activerecord_test/feature/relations/test_many_to_many.py
"""
多对多关系测试

直接导入并运行testsuite的多对多关系测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.relations.test_many_to_many import *

# tests/rhosocial/activerecord_test/feature/query/test_where.py
"""
条件查询测试

直接导入并运行testsuite的条件查询测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.query.test_where import *

# tests/rhosocial/activerecord_test/feature/query/test_joins.py
"""
表连接测试

直接导入并运行testsuite的表连接测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.query.test_joins import *

# tests/rhosocial/activerecord_test/feature/query/test_aggregates.py
"""
聚合查询测试

直接导入并运行testsuite的聚合查询测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.query.test_aggregates import *

# tests/rhosocial/activerecord_test/realworld/test_blog_system.py
"""
博客系统场景测试

直接导入并运行testsuite的博客系统场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_blog_system import *

# tests/rhosocial/activerecord_test/realworld/test_user_management.py
"""
用户管理场景测试

直接导入并运行testsuite的用户管理场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_user_management import *

# tests/rhosocial/activerecord_test/realworld/test_ecommerce.py
"""
电商系统场景测试

直接导入并运行testsuite的电商系统场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_ecommerce import *

# tests/rhosocial/activerecord_test/realworld/test_social_network.py
"""
社交网络场景测试

直接导入并运行testsuite的社交网络场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_social_network import *

# tests/rhosocial/activerecord_test/benchmark/test_crud_performance.py
"""
CRUD操作性能测试

直接导入并运行testsuite的CRUD操作性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_crud_performance import *

# tests/rhosocial/activerecord_test/benchmark/test_query_performance.py
"""
查询性能测试

直接导入并运行testsuite的查询性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_query_performance import *

# tests/rhosocial/activerecord_test/benchmark/test_bulk_operations.py
"""
批量操作性能测试

直接导入并运行testsuite的批量操作性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_bulk_operations import *

# tests/rhosocial/activerecord_test/benchmark/test_concurrent_access.py
"""
并发访问性能测试

直接导入并运行testsuite的并发访问性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_concurrent_access import *
```python
# tests/rhosocial/activerecord_test/basic/test_crud.py
"""
基础CRUD功能测试

直接导入并运行testsuite的基础CRUD测试。
"""

# 设置环境变量（如果还没设置）
import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

# 确保Provider已注册
from tests.providers.registry import provider_registry

# 直接导入testsuite测试，pytest会自动发现
from rhosocial.activerecord.testsuite.feature.basic.test_crud import *

# tests/rhosocial/activerecord_test/basic/test_fields.py
"""
字段类型处理和转换测试

直接导入并运行testsuite的字段类型测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.basic.test_fields import *

# tests/rhosocial/activerecord_test/basic/test_validation.py
"""
数据验证机制测试

直接导入并运行testsuite的数据验证测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.basic.test_validation import *

# tests/rhosocial/activerecord_test/relations/test_has_many.py
"""
一对多关系测试

直接导入并运行testsuite的一对多关系测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.relations.test_has_many import *

# tests/rhosocial/activerecord_test/relations/test_belongs_to.py
"""
多对一关系测试

直接导入并运行testsuite的多对一关系测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.relations.test_belongs_to import *

# tests/rhosocial/activerecord_test/relations/test_many_to_many.py
"""
多对多关系测试

直接导入并运行testsuite的多对多关系测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.relations.test_many_to_many import *

# tests/rhosocial/activerecord_test/query/test_where.py
"""
条件查询测试

直接导入并运行testsuite的条件查询测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.query.test_where import *

# tests/rhosocial/activerecord_test/query/test_joins.py
"""
表连接测试

直接导入并运行testsuite的表连接测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.query.test_joins import *

# tests/rhosocial/activerecord_test/query/test_aggregates.py
"""
聚合查询测试

直接导入并运行testsuite的聚合查询测试。
"""

import os
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.feature.query.test_aggregates import *

# tests/rhosocial/activerecord_test/realworld/test_blog_system.py
"""
博客系统场景测试

直接导入并运行testsuite的博客系统场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_blog_system import *

# tests/rhosocial/activerecord_test/realworld/test_user_management.py
"""
用户管理场景测试

直接导入并运行testsuite的用户管理场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_user_management import *

# tests/rhosocial/activerecord_test/realworld/test_ecommerce.py
"""
电商系统场景测试

直接导入并运行testsuite的电商系统场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_ecommerce import *

# tests/rhosocial/activerecord_test/realworld/test_social_network.py
"""
社交网络场景测试

直接导入并运行testsuite的社交网络场景测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_REALWORLD_TESTS", "false").lower() == "true",
    reason="Realworld tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.realworld.test_social_network import *

# tests/rhosocial/activerecord_test/benchmark/test_crud_performance.py
"""
CRUD操作性能测试

直接导入并运行testsuite的CRUD操作性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_crud_performance import *

# tests/rhosocial/activerecord_test/benchmark/test_query_performance.py
"""
查询性能测试

直接导入并运行testsuite的查询性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_query_performance import *

# tests/rhosocial/activerecord_test/benchmark/test_bulk_operations.py
"""
批量操作性能测试

直接导入并运行testsuite的批量操作性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_bulk_operations import *

# tests/rhosocial/activerecord_test/benchmark/test_concurrent_access.py
"""
并发访问性能测试

直接导入并运行testsuite的并发访问性能测试。
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_BENCHMARK_TESTS", "false").lower() == "true",
    reason="Benchmark tests disabled by environment variable"
)

os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

from tests.providers.registry import provider_registry
from rhosocial.activerecord.testsuite.benchmark.test_concurrent_access import *
```

### 4.2 核心注册机制
```python
# tests/providers/registry.py
from rhosocial.activerecord.testsuite.core.registry import ProviderRegistry
from .basic import BasicProvider

# Create a single, global instance of the ProviderRegistry.
provider_registry = ProviderRegistry()

# Register the concrete `BasicProvider` as the implementation for the
# `feature.basic.IBasicProvider` interface defined in the testsuite.
# When the testsuite needs to run a "basic" feature test, it will ask the registry
# for the "feature.basic.IBasicProvider" and will receive our `BasicProvider`.
provider_registry.register("feature.basic.IBasicProvider", BasicProvider)

# As we migrate more test groups (e.g., relations, query), we will add
# their provider registrations here.
#
# Example:
# from .relations import RelationsProvider
# provider_registry.register("feature.relations.IRelationsProvider", RelationsProvider)
```

## 五、pytest配置文件（修订版）

### 5.1 pytest.ini配置
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src/rhosocial/activerecord
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    feature: 核心功能测试（必须运行）
    realworld: 真实场景测试（可选）
    benchmark: 性能基准测试（可选）
    slow: 运行较慢的测试
    integration: 集成测试

# 过滤警告
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### 5.2 pyproject.toml配置（修订版）
```toml
# pyproject.toml 中的测试配置部分
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"] 
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src/rhosocial/activerecord",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]

markers = [
    "feature: 核心功能测试（必须运行）",
    "realworld: 真实场景测试（可选）",
    "benchmark: 性能基准测试（可选）",
    "slow: 运行较慢的测试",
    "integration: 集成测试",
]

filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

[tool.coverage.run]
source = ["src/rhosocial/activerecord"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__init__.py",
    "*/testsuite/*",                      # 明确排除testsuite
    "*/activerecord/testsuite/*",         # 排除testsuite子包
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### 5.3 conftest.py配置
```python
# tests/conftest.py
"""
后端包测试配置

自动配置Provider注册表，并提供便捷的testsuite集成。
"""

import os
import sys
import pytest

# 确保可以导入Provider
sys.path.insert(0, os.path.dirname(__file__))

# 自动设置Provider注册表路径
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'tests.providers.registry:provider_registry'
)

# 导入注册表以确保Provider被注册
from tests.providers.registry import provider_registry

def pytest_configure(config):
    """配置pytest运行环境"""
    # 注册自定义标记
    config.addinivalue_line("markers", "feature: 核心功能测试（必须运行）")
    config.addinivalue_line("markers", "realworld: 真实场景测试（可选）")
    config.addinivalue_line("markers", "benchmark: 性能基准测试（可选）")
    
    # 环境检查和诊断
    _check_testsuite_environment()

def _check_testsuite_environment():
    """检查testsuite环境设置"""
    try:
        import rhosocial.activerecord.testsuite
        print("✓ testsuite已安装")
    except ImportError:
        print("✗ testsuite未安装，请运行: pip install rhosocial-activerecord-testsuite")
        return
    
    # 检查注册表
    print(f"✓ 注册表已加载，包含 {len(provider_registry._providers)} 个Provider")
    
    # 检查必要的Provider是否已注册
    required_providers = [
        "feature.basic.IBasicProvider",
        "feature.relations.IRelationsProvider", 
        "feature.query.IQueryProvider",
    ]
    
    for provider in required_providers:
        if provider_registry.get_provider(provider):
            print(f"✓ {provider} 已注册")
        else:
            print(f"✗ {provider} 未注册")

def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--test-scenarios",
        action="store",
        default=None,
        help="指定要运行的测试场景，用逗号分隔（如：memory,debug）"
    )
    
    parser.addoption(
        "--skip-testsuite",
        action="store_true",
        default=False,
        help="跳过testsuite测试，只运行本地测试"
    )

def pytest_runtest_setup(item):
    """测试运行前的设置"""
    # 处理测试场景过滤
    test_scenarios = item.config.getoption("--test-scenarios")
    if test_scenarios:
        scenarios = [s.strip() for s in test_scenarios.split(",")]
        os.environ["ENABLED_TEST_SCENARIOS"] = ",".join(scenarios)
    
    # 处理跳过testsuite选项
    if item.config.getoption("--skip-testsuite"):
        # 如果文件路径包含testsuite相关，则跳过
        if "testsuite" in str(item.fspath) or "test_feature_" in str(item.fspath):
            pytest.skip("跳过testsuite测试")
```

## 六、便捷的使用方式

### 6.1 开发者常用命令
```bash
# 在后端包根目录下运行所有测试（包括testsuite）
pytest

# 只运行核心功能测试
pytest -m feature

# 只运行本地集成测试，跳过testsuite
pytest --skip-testsuite

# 运行特定测试场景
pytest --test-scenarios="memory,debug"

# 运行包含数据库特定测试（SQLite专用）
TEST_SQLITE_DEBUG=true TEST_SQLITE_PERFORMANCE=true pytest

# 跳过可选测试
SKIP_REALWORLD_TESTS=true SKIP_BENCHMARK_TESTS=true pytest

# 生成覆盖率报告
pytest --cov=src/rhosocial/activerecord --cov-report=html

# 运行特定测试文件
pytest tests/test_feature_basic.py

# 运行特定测试并显示详细输出
pytest tests/test_feature_basic.py::test_user_crud -v -s
```

### 6.2 环境变量配置
```bash
# 配置SQLite测试（rhosocial-activerecord）
export TEST_SQLITE_FILE=true
export TEST_SQLITE_DEBUG=true
export TEST_SQLITE_PERFORMANCE=true
export TEST_SQLITE_CONCURRENT=true

# 配置MySQL测试（rhosocial-activerecord-mysql）
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=test_db
export TEST_MYSQL_DOCKER=true
export TEST_MYSQL_PERFORMANCE=true

# 配置PostgreSQL测试（rhosocial-activerecord-postgresql）
export PG_HOST=localhost
export PG_PORT=5432
export PG_USER=postgres
export PG_PASSWORD=password
export PG_DATABASE=test_db

# 指定测试场景
export ENABLED_TEST_SCENARIOS="memory,debug"  # SQLite场景
export ENABLED_TEST_SCENARIOS="local,docker"  # MySQL场景

# 跳过可选测试
export SKIP_REALWORLD_TESTS=true
export SKIP_BENCHMARK_TESTS=true
```

### 6.3 CI/CD配置示例
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test-sqlite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.8"
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install rhosocial-activerecord-testsuite[dev]
          pip install pytest-cov pytest-html
      
      - name: Run SQLite tests
        run: pytest -m feature --cov=src --cov-report=xml
        env:
          ENABLED_TEST_SCENARIOS: "memory,debug"
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  test-mysql:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
    
    steps:
      - uses: actions/checkout@v3
        with:
          repository: rhosocial/python-activerecord-mysql
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.8"
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install rhosocial-activerecord-testsuite[dev]
          pip install mysql-connector-python
      
      - name: Run MySQL tests
        env:
          ENABLED_TEST_SCENARIOS: "local"
          MYSQL_HOST: localhost
          MYSQL_PASSWORD: password
        run: pytest --test-scenarios="local" -v
```

## 七、迁移步骤（保持原时间表）

### 第一阶段：建立基础架构（第1-2周）

#### 步骤1.1：创建testsuite项目
```bash
# 创建新仓库
mkdir rhosocial/python-activerecord-testsuite
cd rhosocial/python-activerecord-testsuite

# 初始化项目
poetry init
poetry add pytest pytest-cov
```

#### 步骤1.2：实现核心机制
```python
# src/rhosocial/activerecord/testsuite/core/registry.py
import os
import importlib
from typing import Optional, Type, Dict

class ProviderRegistry:
    """Provider注册表基类"""
    
    def __init__(self):
        self._providers: Dict[str, Type] = {}
    
    def register(self, interface_path: str, provider_class: Type) -> None:
        """注册Provider实现"""
        self._providers[interface_path] = provider_class
    
    def get_provider(self, interface_path: str) -> Optional[Type]:
        """获取Provider实现"""
        return self._providers.get(interface_path)

def get_provider_registry() -> ProviderRegistry:
    """获取全局Provider注册表"""
    registry_path = os.environ.get('TESTSUITE_PROVIDER_REGISTRY')
    if not registry_path:
        raise RuntimeError(
            "未设置 TESTSUITE_PROVIDER_REGISTRY 环境变量。\n"
            "请设置为注册表对象的导入路径，如:\n"
            "export TESTSUITE_PROVIDER_REGISTRY="
            "'tests.providers.registry:provider_registry'"
        )
    
    module_path, obj_name = registry_path.rsplit(':', 1)
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)
```

### 第二阶段：迁移基础功能测试（第2-3周）

#### 步骤2.1：迁移basic测试组
1. 在testsuite中创建 `feature/basic/` 目录
2. 定义 `IBasicProvider` 接口
3. 迁移测试文件：
   - `test_crud.py`
   - `test_fields.py` 
   - `test_validation.py`

#### 步骤2.2：在rhosocial-activerecord中建立集成
```bash
# 在rhosocial/python-activerecord目录下
pip install rhosocial-activerecord-testsuite

# 创建tests/目录结构
mkdir -p tests/providers tests/fixtures/schemas/sqlite tests/fixtures/data
```

#### 步骤2.3：创建简化的场景配置和集成文件
```python
# tests/providers/scenarios.py
# (见上面的简化场景配置实现)

# tests/test_feature_basic.py
# (见上面的直接导入测试实现)
```

### 第三阶段：验证和调试（第3-4周）

#### 步骤3.1：本地测试验证
```bash
# 在rhosocial/python-activerecord目录下运行
pytest  # 运行所有测试，包括testsuite

# 验证覆盖率（排除testsuite）
pytest --cov=src/rhosocial/activerecord --cov-report=html

# 测试不同场景
TEST_SQLITE_DEBUG=true pytest --test-scenarios="debug"
```

### 第四阶段：增量迁移其他测试（第4-8周）

按优先级迁移其他测试组：
1. **relations** - 关系测试（第4-5周）
2. **query** - 查询测试（第5-6周）  
3. **realworld** - 真实场景测试（第6-7周）
4. **benchmark** - 性能测试（第7-8周）

每个阶段的模式相同：
1. 在testsuite中定义接口和测试
2. 在后端包中创建集成文件（直接导入）
3. 实现对应的Provider
4. 在scenarios.py中添加必要的场景支持
5. 测试验证

## 八、成功标准

- ✅ 所有现有测试成功迁移并运行通过
- ✅ **后端专注性**：testsuite独立于具体数据库后端，每个后端包只负责自己的测试
- ✅ **简化配置**：使用简单的场景映射表，针对单一后端类型的不同配置
- ✅ **直接导入**：通过直接导入测试实现集成，降低复杂度
- ✅ **覆盖率正确**：覆盖率统计正确排除testsuite代码
- ✅ **多场景支持**：单一后端支持多种测试场景（如内存数据库、文件数据库、调试模式等）
- ✅ 测试运行时间不超过原来的110%
- ✅ 清晰的文档和示例
- ✅ CI/CD完整集成
- ✅ **便捷性**：开发者只需运行 `pytest` 即可执行完整测试套件
- ✅ **后端特定性**：每个后端的schema、环境准备、清理机制都由该后端实现
- ✅ **开发者友好**：后端开发者只需提供简单的场景配置和Provider实现
- ✅ **扩展性**：其他后端包可以独立实现自己的testsuite集成

## 九、与其他后端包的关系

### 9.1 责任分离
- **rhosocial-activerecord**：提供SQLite后端的完整testsuite集成示例
- **rhosocial-activerecord-mysql**：独立实现MySQL后端的testsuite集成
- **rhosocial-activerecord-postgresql**：独立实现PostgreSQL后端的testsuite集成

### 9.2 用户使用场景
```bash
# 用户只使用SQLite（默认）
pip install rhosocial-activerecord rhosocial-activerecord-testsuite
cd my-project && pytest  # 运行SQLite相关测试

# 用户使用MySQL
pip install rhosocial-activerecord-mysql rhosocial-activerecord-testsuite
cd my-project && pytest  # 运行MySQL相关测试

# 用户想对比不同后端（需要分别测试）
# 1. 测试SQLite版本
git clone my-project-sqlite && cd my-project-sqlite
pytest  # SQLite测试结果

# 2. 测试MySQL版本  
git clone my-project-mysql && cd my-project-mysql
# 修改配置使用MySQL后端
pytest  # MySQL测试结果

# 3. 手动对比结果
```

### 9.3 文档指导原则
在testsuite文档中明确说明：

1. **场景命名规范**：
   - 场景名只与当前后端相关，不包含后端类型前缀
   - SQLite后端使用："memory", "tempfile", "debug" 等
   - MySQL后端使用："local", "docker", "performance" 等
   - PostgreSQL后端使用："local", "replica1", "replica2" 等

2. **配置方式优先级**：
   - 环境变量作为主要配置方式
   - 支持环境变量覆盖默认值

3. **测试执行原则**：
   - testsuite提供标准化的测试用例
   - 每个后端包独立实现和维护自己的测试集成
   - 不提供跨后端自动化对比功能
   - 如需对比不同后端，建议用户分别运行各后端的测试并手动对比结果

4. **多实例测试支持**：
   - 通过环境变量定义多个场景
   - 支持测试同一后端的不同配置（如多个MySQL服务器）
   - 便于持续集成中的矩阵测试

5. **开发者指南**：
   ```bash
   # 查看当前后端可用场景
   pytest --collect-only | grep scenario
   
   # 使用特定场景
   pytest --test-scenarios=debug
   
   # 使用环境变量配置
   TEST_SQLITE_DEBUG=true pytest
   ```

6. **持续集成建议**：
   - 在CI配置中使用环境变量配置场景
   - 每个后端包维护自己的CI配置
