# PyCharm Integration Guide

This document provides detailed steps for seamlessly integrating the `rhosocial-activerecord-testsuite` with the PyCharm IDE, allowing developers to leverage PyCharm's powerful features for running tests and analyzing code coverage.

## 1. Configure the Default Test Runner

First, you need to tell PyCharm that this project uses `pytest` as its testing framework.

1.  Open PyCharm's settings: `Preferences` (macOS) or `Settings` (Windows/Linux).
2.  Navigate to `Tools` > `Python Integrated Tools`.
3.  In the `Testing` section, select `pytest` from the `Default test runner` dropdown menu.
4.  Click `Apply` to save the settings.

## 2. Configure the Project Interpreter

Ensure that PyCharm is using the virtual environment that contains all the project dependencies (like `pytest`, `pytest-cov`, etc.).

1.  In settings, navigate to `Project: python-activerecord-testsuite` > `Python Interpreter`.
2.  Check if the currently selected interpreter points to your project's virtual environment (e.g., an interpreter path containing `.venv` or `venv`).
3.  If not, click the gear icon, select `Add...`, and locate the `python` executable within your project's virtual environment.

## 3. Running Tests

Once configured, you can run tests conveniently:

-   **Single Test**: In the code editor, click the green play button next to a test function or class.
-   **Single File**: In the Project view, right-click a test file (e.g., `test_crud.py`) and select `Run 'pytest in test_crud.py'`.
-   **Entire Directory**: In the Project view, right-click a directory (e.g., `basic`) and select `Run 'pytest in basic'`.

PyCharm will display the formatted test results in the "Run" tool window.

## 4. Running with Code Coverage

PyCharm can automatically use `pytest-cov` to collect and display code coverage.

1.  **Run with Coverage**: Right-click the file or directory you want to test and select `Run 'pytest in ...' with Coverage`.

2.  **Configure Coverage Target**: By default, PyCharm might measure the coverage of the test code itself. To properly measure the coverage of the `rhosocial-activerecord` library, you need to configure the run template once:
    a.  First, run a coverage test once as described above.
    b.  Click the `Run` > `Edit Configurations...` menu item.
    c.  In the `Pytest` list on the left, find the configuration you just ran (e.g., `pytest in basic`).
    d.  In the `Additional Arguments` field on the right, add `--cov=rhosocial.activerecord`.
    e.  Click `Apply` to save.

3.  **View Results**: Run the test with `... with Coverage` again. Now, PyCharm will:
    *   Display a detailed coverage report for the `rhosocial.activerecord` package in the "Coverage" tool window, showing file and line coverage percentages.
    *   Visually mark code lines in the editor with green (covered) and red (uncovered) bars.

With this setup, you can efficiently run tests and analyze coverage entirely within the PyCharm graphical interface.
