# 测试套件文档

本文档提供了使用测试套件的全面指南。

## 目录

- [简介](README.md)
- [配置](configuration.md)
- [运行测试](running_tests.md)
- [故障排除](troubleshooting.md)
- [贡献](contributing.md)

## 1. 简介

欢迎使用 ActiveRecord 测试套件。该软件包为所有与 `rhosocial-activerecord` 库集成的数据库后端提供了一套标准化的测试合约。

其主要目标是确保每个后端（无论是官方的还是第三方的）都遵循核心库所期望的一致且正确的行为。测试套件基于以下三大支柱构建：

-   **功能测试**：验证独立的、原子性的功能（例如，CRUD 操作、查询方法、字段类型）。
-   **真实场景测试**：模拟复杂的业务逻辑，测试不同组件之间的交互。
-   **性能基准测试**：衡量和比较不同后端之间的性能指标。

## 2. 后端开发者入门

要使用此测试套件来验证您的自定义数据库后端，请遵循以下步骤：

### 先决条件

-   一个可工作的数据库后端实现，它继承自 `rhosocial.activerecord.backend.StorageBackend`。
-   您的后端包应该可以在测试环境中安装。

### 安装

在您的后端项目的 `pyproject.toml` 中，将 `rhosocial-activerecord-testsuite` 添加为开发依赖项：

```toml
[project.optional-dependencies]
dev = [
    "rhosocial-activerecord-testsuite>=0.1.0",
    "pytest-cov>=4.0.0"
]
```