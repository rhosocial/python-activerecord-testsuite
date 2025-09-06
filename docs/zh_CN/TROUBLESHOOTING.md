# 测试套件常见问题与调试指南

本文档记录了在运行 `rhosocial-activerecord-testsuite` 时可能遇到的一些常见问题、错误及其解决方案。这些经验来自于一次完整的调试过程, 旨在帮助后端开发者快速定位和解决问题。

## 1. 环境配置问题

在运行测试之前, 一个正确配置的 Python 和依赖环境至关重要。

### 错误: `poetry: command not found`

**原因**:

`poetry` 未被安装, 或者其安装路径没有被添加到系统的 `PATH` 环境变量中。

**解决方案**:

1.  **推荐**: 确保 `poetry` 已正确安装并配置在 `PATH` 中。
2.  **备选方案**: 如果您不想或不能将 `poetry` 加入 `PATH`, 您可以直接使用由 `poetry` 创建的虚拟环境中的 Python 解释器来运行 `pytest`。假设您的虚拟环境在项目目录下的 `.venv3.13` 中:

    ```bash
    # 在项目根目录执行
    .venv3.13/bin/python -m pytest src/rhosocial/activerecord/testsuite/feature/
    ```

### 错误: `ModuleNotFoundError: No module named 'email_validator'`

**原因**:

测试环境缺少必要的依赖。`pydantic` 的 `EmailStr` 类型需要 `email-validator` 包的支持, 但它可能没有被正确安装。

**解决方案**:

使用虚拟环境中的 `pip` 来安装缺失的依赖。`pydantic` 通过 "extras" 机制来管理这些可选依赖。

```bash
.venv3.13/bin/python -m pip install "pydantic[email]"
```

### 错误: `SSL: CERTIFICATE_VERIFY_FAILED`

**原因**:

在 `pip` 安装依赖时, 发生了 SSL 证书验证错误。这通常发生在公司网络或配置了网络代理的环境中, 您的系统无法验证 PyPI 的 SSL 证书。

**解决方案**:

在 `pip` 命令中添加 `--trusted-host` 参数, 以信任 PyPI 的主机。这是一种在受限网络中常见的解决方法。

```bash
.venv3.13/bin/python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org "pydantic[email]"
```

## 2. 测试代码与核心库 API 不匹配

当测试套件与 `rhosocial-activerecord` 核心库版本不完全匹配时, 可能会出现一系列的 `TypeError` 和 `AttributeError`。

### 调试过程回顾

在一次调试中, 我们遇到了以下连续的错误, 这揭示了测试夹具 (fixture) 设计上的问题:

1.  **`TypeError: BaseActiveRecord.configure() got an unexpected keyword argument 'backend'`**
    *   **问题**: `conftest.py` 中的 `user_class` 等 fixture 错误地以 `User.configure(backend=db_session)` 的方式调用模型配置方法。
    *   **分析**: `ActiveRecord` 的 `configure` 方法需要的是 `config` (连接配置对象) 和 `backend_class` (后端类), 而不是一个 `backend` 的实例。

2.  **`AttributeError: 'dict' object has no attribute 'connection_config'`**
    *   **问题**: 在修复上一个问题后, 我们尝试 `User.configure(config=db_session.connection_config, ...)`。但这导致了新错误, 因为 `db_session` 参数实际上是 `pytest` 参数化传入的配置字典 (`dict`), 而不是 `backend` 实例。
    *   **分析**: 对 `pytest` fixture 的参数化机制理解有误。直接参数化的 fixture 会将参数值本身注入, 而不是 fixture 的执行结果。

3.  **`AttributeError: 'SQLiteBackend' object has no attribute 'connection_config'`** 和 **`'SQLiteBackend' object has no attribute 'name'`**
    *   **问题**: 在通过 `indirect=True` 修正了 fixture 的执行流程后, 发现 `backend` 实例上并不存在 `connection_config` 和 `name` 这样的属性。
    *   **分析**: 这些信息存在于测试开始时加载的原始 `config` 字典中, 而没有被存储在 `backend` 实例上。

### 最终解决方案: 重构 Fixture

为了彻底解决问题, 我们对 `conftest.py` 和 `utils/helpers.py` 进行了重构, 以确保所有需要的信息都能被正确地创建和传递。

1.  **`helpers.py` 的修改**:
    *   `setup_database` 函数被修改为返回一个元组 `(backend, connection_config)`, 同时包含 `backend` 实例和它所使用的 `connection_config` 对象。
    *   `teardown_database` 函数被修改为接受 `backend_name` 参数, 以便在日志中输出更清晰的信息。

2.  **`conftest.py` 的修改**:
    *   `database` fixture (原名 `db_session`) 使用 `indirect=True` 进行参数化。
    *   `database` fixture 调用 `setup_database`, 然后 `yield` 出包含 `backend` 实例和 `connection_config` 对象的元组。
    *   在 `teardown` 阶段, `database` fixture 调用 `teardown_database` 时, 会从原始的 `config` 字典中传入 `backend_name`。
    *   所有依赖于它的模型 fixture (如 `user_class`) 会接收这个元组, 解包后获得所需的对象, 并正确地调用 `User.configure()`。

这个重构后的结构保证了数据流的清晰和正确, 是编写健壮测试套件的良好实践。

## 3. 解决测试警告和后续错误

在主要错误修复后, 测试可能仍然会失败或显示警告。以下是最终解决所有问题的步骤。

### 错误: `sqlite3.OperationalError: table users already exists`

*   **原因**: 尽管 `teardown_database` 在每个测试后被调用, 但其中的 `DROP TABLE` 语句没有被正确地提交到数据库。这是因为 `ActiveRecord` 库的 `execute` 方法默认只为 DML 语句 (如 `INSERT`, `UPDATE`) 自动提交事务, 而 `DROP TABLE` 是 DDL 语句。
*   **解决方案**: 修改 `testsuite/utils/helpers.py` 中的 `teardown_database` 函数, 将所有 `DROP TABLE` 语句包裹在一个事务中, 以确保它们被正确提交。

    ```python
    def teardown_database(backend, backend_name):
        # ...
        try:
            with backend.transaction():
                backend.execute("DROP TABLE IF EXISTS users;")
                backend.execute("DROP TABLE IF EXISTS type_cases;")
                backend.execute("DROP TABLE IF EXISTS validated_field_users;")
        # ...
    ```

### 警告: `PytestConfigWarning: Unknown config option: python_paths`

*   **原因**: `pytest` 在其配置文件 (`pyproject.toml` 的 `[tool.pytest.ini_options]` 部分) 中发现了一个它不认识的配置项 `python_paths`。
*   **解决方案**: 编辑 `pyproject.toml` 文件, 将 `python_paths = ["src"]` 这一行从 `[tool.pytest.ini_options]` 段落中删除。

### 警告: `Pydantic serializer warnings` (Decimal 到 float 的转换)

*   **原因**: 在测试代码中, 一个 `Decimal` 类型的高精度数值被赋给了一个 `float` 类型的模型字段。Pydantic 出于严谨发出了警告, 因为这个转换过程可能会损失精度。
*   **解决方案**: 修改 `test_crud.py` 中的测试用例, 确保赋给 `balance` 字段的值是 `float` 类型, 而不是 `Decimal` 类型。例如, 将 `Decimal("100.50")` 修改为 `100.50`。

### 警告: `ConnectionError` (在测试退出时)

*   **原因**: 在所有测试执行完毕, Python 解释器准备退出时, `SQLiteBackend` 的 `__del__` 方法被调用以进行最后的清理。但此时, 它所依赖的一些模块 (如 `os` 或 `sys`) 可能已经被卸载, 导致在尝试删除数据库文件时出错。
*   **解决方案**: 这是一个库级别的缺陷。通过修改 `python-activerecord` 项目中的 `src/rhosocial/activerecord/backend/impl/sqlite/backend.py` 文件, 使用 `atexit` 模块来注册一个可靠的文件清理函数, 并将文件删除逻辑从 `disconnect` 方法中移除, 从而彻底解决了该问题。

    ```python
    # 在 SQLiteBackend 的 __init__ 方法中添加:
    if self.config.delete_on_close and not self.config.is_memory_db():
        import atexit
        atexit.register(self._delete_db_files)

    # 并将文件删除逻辑移到一个新的 _delete_db_files 方法中。
    ```