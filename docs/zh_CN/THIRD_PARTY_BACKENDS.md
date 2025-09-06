# 第三方后端集成指南

`rhosocial-activerecord-testsuite` 的核心设计目标之一就是可扩展性, 允许任何第三方数据库后端无缝接入, 并使用本套件来验证其与 `rhosocial-activerecord` 的兼容性。

本指南将详细说明一个第三方后端需要满足的条件和配置步骤。

## 1. 核心机制: Entry Points

本测试套件通过 Python 标准的 `entry_points` (入口点) 机制来自动发现和加载后端驱动。这意味着, 任何想要被本套件识别的后端库, 都必须将自己注册为一个特定的入口点。

## 2. 集成步骤

假设您正在开发一个名为 `acme-corp-superdb` 的后端库, 其驱动类为 `AcmeDBBackend`。

### 步骤一: 在您的后端库中注册入口点

在您的 `acme-corp-superdb` 项目的 `pyproject.toml` 文件中, 添加以下内容:

```toml
[project.entry-points."rhosocial.activerecord.backend"]
acme_db = "acme_corp.activerecord.backend.impl.acme_db:AcmeDBBackend"
```

- **`[project.entry-points."rhosocial.activerecord.backend"]`**: 这是一个固定的入口点组名, 所有后端都必须注册在这个组下。
- **`acme_db`**: 这是您为您的驱动定义的“简称”。这个简称非常重要, 它将作为 `driver` 的值在 `backends.yml` 中被使用。
- **`"acme_corp.activerecord.backend.impl.acme_db:AcmeDBBackend"`**: 这是您的后端驱动主类的完整、可导入的路径。

### 步骤二: 安装您的后端库

确保您的 `acme-corp-superdb` 库已经以可编辑模式 (`pip install -e .`) 或普通模式安装到了您运行测试套件的同一个 Python 虚拟环境中。

### 步骤三: 配置测试实例

您可以通过两种方式来配置要测试的数据库实例, **环境变量的优先级高于 `backends.yml` 文件**。

#### 方式一: 使用 `backends.yml` 文件 (推荐用于本地开发)

在 `python-activerecord-testsuite` 项目的根目录下, 创建或修改 `backends.yml` 文件:

```yaml
acme:
  acme_test_instance_1:
    driver: acme_db
    host: "db.acme.com"
    port: 9999
    username: "test_user"
    password: "secret"
    database: "testsuite_db_for_acme"
```

#### 方式二: 使用环境变量 (推荐用于 CI/CD)

您可以在执行 `pytest` 的环境中设置一系列环境变量来定义一个或多个测试目标。通过在变量名末尾添加 `_1`, `_2` 来区分不同的配置。

例如, 定义一个名为 `mysql_ci` 的测试目标:
```bash
export AR_TEST_BACKEND_NAME_1=mysql_ci
export AR_TEST_BACKEND_DRIVER_1=mysql
export AR_TEST_BACKEND_HOST_1=127.0.0.1
export AR_TEST_BACKEND_PORT_1=3306
export AR_TEST_BACKEND_USER_1=root
export AR_TEST_BACKEND_PASSWORD_1=password
export AR_TEST_BACKEND_DATABASE_1=test_db
```

## 3. 执行测试

完成以上步骤后, 您无需做任何其他修改。直接在 `python-activerecord-testsuite` 项目的根目录下运行 `pytest`:

```bash
pytest
```

测试套件的加载器会自动发现并加载所有配置, 然后运行完整的测试。