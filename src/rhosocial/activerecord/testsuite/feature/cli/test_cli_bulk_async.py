# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_bulk_async.py
"""CLI bulk DML contract tests (asynchronous)."""

import json

from .utils import run_cli_async


class TestAsyncCLIBulk:
    async def test_bulk_create_and_delete(self, async_cli_models):
        code, out, err = await run_cli_async(
            [
                "dml",
                "bulk",
                "create",
                "--model",
                async_cli_models.bulk_model,
                "--data",
                '[{"name": "async_bulk_one", "age": 20},'
                '{"name": "async_bulk_two", "age": 30}]',
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        rows = json.loads(out)
        ids = [row["id"] for row in rows]
        assert len(ids) == 2

        code, out, err = await run_cli_async(
            [
                "dml",
                "bulk",
                "delete",
                "--model",
                async_cli_models.bulk_model,
                "--data",
                json.dumps(ids),
                "--yes",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["affected"] == 2

