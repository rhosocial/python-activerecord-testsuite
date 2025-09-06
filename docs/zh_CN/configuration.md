# 配置指南

本文档详细介绍了测试套件的各种配置选项。

## 1. 灵活的配置系统

测试套件由一个灵活的配置系统驱动，允许您针对多种数据库版本和设置进行测试。

### 后端驱动和命名空间

在配置之前，了解后端是如何加载的非常重要：

-   **官方后端**：由 `rhosocial` 发布的后端安装在 `rhosocial.activerecord.backend.impl` 命名空间下（例如，`...impl.mysql`）。测试套件的默认配置加载器知道如何找到这些后端。
-   **第三方后端**：如果您正在开发第三方后端，它应该位于自己的命名空间中（例如，`acme_corp.activerecord.backend.impl.acme_db`）。要使测试套件识别您的驱动，您需要注册它，通常使用 Python 的 `entry_points` 机制在您的包的 `pyproject.toml` 中进行。

### 内置 SQLite 支持

测试套件包含对 `rhosocial-activerecord` 附带的 `sqlite` 后端的内置支持。配置由您用于运行测试的 Python 版本决定。

-   **自动检测**：默认情况下，测试套件会检测当前的 Python 版本（例如，3.11）并针对其相应的 SQLite 版本运行测试（例如，`sqlite_py311_mem` 和 `sqlite_py311_file`）。
-   **CI/CD 覆盖**：您可以通过设置 `PYTEST_TARGET_VERSION` 环境变量来强制测试针对特定 Python 版本的配置运行。例如：
    ```bash
    PYTEST_TARGET_VERSION=3.10 pytest
    ```

### 自定义后端配置

要测试您自己的后端（或其他可选后端，如 MySQL、PostgreSQL），您需要配置连接详细信息。这可以通过使用环境变量来完成。

#### 使用环境变量（推荐）

您可以通过在执行 `pytest` 的 shell 中设置一系列环境变量来定义一个或多个测试目标。使用数字后缀（`_1`、`_2` 等）来区分不同的配置。

例如，要定义一个名为 `mysql_ci` 的测试目标：
```bash
export AR_TEST_BACKEND_NAME_1=mysql_ci
export AR_TEST_BACKEND_DRIVER_1=mysql
export AR_TEST_BACKEND_HOST_1=127.0.0.1
export AR_TEST_BACKEND_PORT_1=3306
export AR_TEST_BACKEND_USER_1=root
export AR_TEST_BACKEND_PASSWORD_1=password
export AR_TEST_BACKEND_DATABASE_1=test_db
```
