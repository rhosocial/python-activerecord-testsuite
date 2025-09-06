# 持续集成 (CI/CD) 指南

本指南提供了在持续集成 (CI/CD) 环境中配置和运行 `rhosocial-activerecord-testsuite` 的最佳实践, 以实现对您的数据库后端的自动化测试。

## 核心策略: 矩阵构建与服务容器

为了在多种 Python 版本和多种数据库上进行全面的测试, 我们强烈推荐使用“矩阵构建 (Matrix Build)”策略。这允许您为每个 Python 版本和数据库的组合自动创建一个独立的测试任务。

GitHub Actions 对此提供了原生支持, 是我们的首选平台。

## GitHub Actions 工作流示例

以下是一个 `.github/workflows/ci.yml` 文件的示例, 您可以将其作为模板集成到您的项目中。

```yaml
name: Python Package CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:

    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
        # 定义您想测试的数据库服务
        database:
          - name: mysql
            image: mysql:8.0
            port: 3306
            env:
              MYSQL_ROOT_PASSWORD: password
              MYSQL_DATABASE: test_db
          - name: postgres
            image: postgres:15
            port: 5432
            env:
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
              POSTGRES_DB: test_db

    # 使用服务容器来启动数据库
    services:
      db:
        image: ${{ matrix.database.image }}
        env: ${{ matrix.database.env }}
        ports:
          - ${{ matrix.database.port }}:${{ matrix.database.port }}

    steps:
    - uses: actions/checkout@v3
      with:
        # 获取所有历史记录, 以便进行版本相关的操作
        fetch-depth: 0

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: 安装依赖
      run: |
        python -m pip install --upgrade pip
        # 如果您的后端依赖 rhosocial-activerecord, 请先安装它
        # pip install rhosocial-activerecord
        # 安装您的后端库 (假设它在当前仓库)
        pip install .
        # 安装测试套件及其依赖
        pip install rhosocial-activerecord-testsuite[test,cov]

    - name: 运行测试 (针对服务容器中的数据库)
      run: |
        pytest --cov=${{ matrix.database.name }} --cov-report=xml
      env:
        # 通过环境变量动态配置测试后端
        AR_TEST_BACKEND_NAME_1: ${{ matrix.database.name }}_ci
        AR_TEST_BACKEND_DRIVER_1: ${{ matrix.database.name }}
        AR_TEST_BACKEND_HOST_1: 127.0.0.1
        AR_TEST_BACKEND_PORT_1: ${{ matrix.database.port }}
        AR_TEST_BACKEND_USER_1: ${{ matrix.database.env.MYSQL_USER || matrix.database.env.POSTGRES_USER }}
        AR_TEST_BACKEND_PASSWORD_1: ${{ matrix.database.env.MYSQL_ROOT_PASSWORD || matrix.database.env.POSTGRES_PASSWORD }}
        AR_TEST_BACKEND_DATABASE_1: ${{ matrix.database.env.MYSQL_DATABASE || matrix.database.env.POSTGRES_DB }}

    - name: 上传覆盖率报告
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }} # 可选
        file: ./coverage.xml
```

### 工作流解析

1.  **矩阵 (Matrix)**: `strategy.matrix` 定义了两个维度的变量: `python-version` 和 `database`。GitHub Actions 会为所有这些变量的组合创建独立的测试任务。例如, `Python 3.8` + `MySQL 8.0`, `Python 3.14` + `PostgreSQL 15` 等。

2.  **服务容器 (Services)**: `services` 块会根据矩阵中的 `database.image` 变量, 使用 Docker 启动一个临时的数据库容器。`ports` 确保了您的测试代码可以通过 `localhost` 和指定的端口访问到这个数据库。

3.  **动态配置**: 在“运行测试”步骤中, 我们没有使用 `backends.yml` 文件, 而是通过 `env` 块将矩阵中的数据库连接信息设置为 `AR_TEST_BACKEND_*` 格式的环境变量。`config.py` 会自动读取这些变量并配置测试目标, 实现了完全的自动化。

4.  **覆盖率**: `--cov` 参数的值也可以从矩阵中动态获取, 从而为每个被测试的后端生成独立的覆盖率报告。

通过这种方式, 您可以轻松地为您的后端库建立一个健壮、可扩展的自动化测试流水线。
