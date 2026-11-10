# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_soft_delete.py
"""CLI soft-delete contract tests (synchronous)."""

import json

import pytest

from .utils import run_cli


class TestCLISoftDelete:
    def test_delete_reports_soft_delete(self, cli_models):
        if cli_models.soft_delete_model is None:
            pytest.skip("Backend provider does not expose a soft-delete model")
        code, out, err = run_cli(
            [
                "dml",
                "create",
                "--model",
                cli_models.soft_delete_model,
                "--data",
                json.dumps({"title": "cli_soft_task"}),
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        task = json.loads(out)
        code, out, err = run_cli(
            [
                "dml",
                "delete",
                "--model",
                cli_models.soft_delete_model,
                "--pk",
                str(task["id"]),
                "--yes",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["action"] == "soft_delete"
