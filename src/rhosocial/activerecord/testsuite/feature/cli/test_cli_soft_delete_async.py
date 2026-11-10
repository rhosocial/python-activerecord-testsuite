# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_soft_delete_async.py
"""CLI soft-delete contract tests (asynchronous)."""

import json

import pytest

from .utils import run_cli_async


class TestAsyncCLISoftDelete:
    async def test_delete_reports_soft_delete(self, async_cli_models):
        if async_cli_models.soft_delete_model is None:
            pytest.skip("Backend provider does not expose a soft-delete model")
        code, out, err = await run_cli_async(
            [
                "dml",
                "create",
                "--model",
                async_cli_models.soft_delete_model,
                "--data",
                json.dumps({"title": "async_cli_soft_task"}),
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        task = json.loads(out)
        code, out, err = await run_cli_async(
            [
                "dml",
                "delete",
                "--model",
                async_cli_models.soft_delete_model,
                "--pk",
                str(task["id"]),
                "--yes",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["action"] == "soft_delete"

