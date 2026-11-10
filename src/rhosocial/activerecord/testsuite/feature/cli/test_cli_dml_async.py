# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_dml_async.py
"""CLI DML contract tests (asynchronous)."""

import json

from .utils import run_cli_async


async def _create(models, username, age):
    code, out, err = await run_cli_async(
        [
            "dml",
            "create",
            "--model",
            models.model,
            "--data",
            json.dumps(
                {"username": username, "email": f"{username}@example.com", "age": age}
            ),
            "-o",
            "json",
        ]
    )
    assert code == 0, err
    return json.loads(out)


class TestAsyncCLIDml:
    async def test_create_list_update_delete(self, async_cli_models):
        user = await _create(async_cli_models, "async_cli_alice", 30)
        code, out, err = await run_cli_async(
            [
                "dql",
                "list",
                "--model",
                async_cli_models.model,
                "--limit",
                "5",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert any(row["id"] == user["id"] for row in json.loads(out))

        code, out, err = await run_cli_async(
            [
                "dml",
                "update",
                "--model",
                async_cli_models.model,
                "--pk",
                str(user["id"]),
                "--data",
                json.dumps({"age": 31}),
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["age"] == 31

        code, out, err = await run_cli_async(
            [
                "dml",
                "delete",
                "--model",
                async_cli_models.model,
                "--pk",
                str(user["id"]),
                "--yes",
                "-o",
                "json",
            ]
        )
        assert code == 0, err

