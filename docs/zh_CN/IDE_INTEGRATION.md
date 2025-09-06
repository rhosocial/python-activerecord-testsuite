# PyCharm 集成指南

本文档为开发者提供将 `rhosocial-activerecord-testsuite` 与 PyCharm IDE 无缝集成的详细步骤, 以便利用 PyCharm 强大的测试和代码覆盖率分析功能。

## 1. 配置默认测试运行器

首先, 需要告知 PyCharm 本项目使用 `pytest` 作为测试框架。

1.  打开 PyCharm 的设置: `Preferences` (macOS) 或 `Settings` (Windows/Linux)。
2.  导航到 `Tools` > `Python Integrated Tools`。
3.  在 `Testing` 部分的 `Default test runner` 下拉菜单中, 选择 `pytest`。
4.  点击 `Apply` 保存设置。

## 2. 配置项目解释器

确保 PyCharm 使用的是包含了所有项目依赖 (如 `pytest`, `pytest-cov` 等) 的虚拟环境。

1.  在设置中, 导航到 `Project: python-activerecord-testsuite` > `Python Interpreter`。
2.  检查当前选择的解释器是否指向您项目的虚拟环境 (例如, 路径中包含 `.venv` 或 `venv` 的解释器)。
3.  如果不是, 请点击齿轮图标, 选择 `Add...`, 并找到您项目的虚拟环境中的 `python` 可执行文件。

## 3. 运行测试

完成以上配置后, 您可以非常方便地运行测试:

-   **单个测试**: 在代码编辑器中, 点击测试函数或测试类旁边的绿色“播放”按钮。
-   **单个文件**: 在项目视图中右键点击一个测试文件 (如 `test_crud.py`), 选择 `Run 'pytest in test_crud.py'`。
-   **整个目录**: 在项目视图中右键点击一个目录 (如 `basic`), 选择 `Run 'pytest in basic'`。

PyCharm 会在 "Run" 工具窗口中展示格式化的测试结果。

## 4. 运行代码覆盖率分析

PyCharm 可以自动利用 `pytest-cov` 来收集和展示代码覆盖率。

1.  **运行带覆盖率的测试**: 右键点击您想测试的文件或目录, 选择 `Run 'pytest in ...' with Coverage`。

2.  **配置覆盖率目标**: 默认情况下, PyCharm 可能会计算测试代码自身的覆盖率。为了让它正确地分析 `rhosocial-activerecord` 库的覆盖率, 您需要进行一次性配置:
    a.  首先, 正常运行一次带覆盖率的测试。
    b.  点击顶部菜单 `Run` > `Edit Configurations...`。
    c.  在左侧的 `Pytest` 列表中, 找到您刚刚运行的那个配置 (例如 `pytest in basic`)。
    d.  在右侧的 `Additional Arguments` 字段中, 添加 `--cov=rhosocial.activerecord`。
    e.  点击 `Apply` 保存。

3.  **查看结果**: 再次以 `... with Coverage` 模式运行测试。现在, PyCharm 会:
    *   在 "Coverage" 工具窗口中展示 `rhosocial.activerecord` 包内每个文件和代码行的覆盖率详情。
    *   在编辑器中, 用绿色 (已覆盖) 和红色 (未覆盖) 的标记条直观地显示代码行的覆盖状态。

通过以上配置, 您就可以完全在 PyCharm 的图形化界面中高效地进行测试和覆盖率分析了。
