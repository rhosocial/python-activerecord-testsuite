# src/rhosocial/activerecord/testsuite/feature/cli/utils.py
"""Helpers for invoking the CLI in-process."""

import asyncio
import io
from contextlib import redirect_stderr, redirect_stdout

from rhosocial.activerecord.backend.dialect.protocols import CTESupport
from rhosocial.activerecord.cli import main


def supports_basic_cte(model) -> bool:
    """Whether the configured model's dialect supports basic CTEs.

    CLI contract tests cannot use the ``requires_protocol`` marker: its
    fixture lives under ``feature/query`` and looks only at query fixtures,
    not at ``cli_models``.
    """
    dialect = model.backend().dialect
    return isinstance(dialect, CTESupport) and dialect.supports_basic_cte()


def run_cli(argv):
    """Run the CLI and return ``(exit_code, stdout, stderr)``."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 0
    return code, out.getvalue(), err.getvalue()


async def run_cli_async(argv):
    """Run the CLI in a worker thread so its own ``asyncio.run`` can start.

    ``main()`` is a process entry point and owns its event loop.  A testsuite
    async test already runs inside one, so invoking ``main()`` directly would
    raise ``asyncio.run() cannot be called from a running event loop``.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, run_cli, argv)
