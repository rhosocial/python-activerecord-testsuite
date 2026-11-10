# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_read_only_async.py
"""CLI read-only model contract tests (asynchronous)."""

from .utils import run_cli_async


class TestAsyncCLIReadOnly:
    async def test_dml_rejected(self, async_cli_models):
        code, out, err = await run_cli_async(
            [
                "dml",
                "create",
                "--model",
                async_cli_models.read_only_model,
                "--data",
                '{"id": 1, "username": "nope"}',
                "-o",
                "json",
            ]
        )
        assert code == 6
        assert out == ""
        assert "read-only" in err

    async def test_dql_still_works(self, async_cli_models):
        code, out, err = await run_cli_async(
            ["dql", "count", "--model", async_cli_models.read_only_model, "-o", "value"]
        )
        assert code == 0, err

