# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_dql_async.py
"""CLI DQL contract tests (asynchronous)."""

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


class TestAsyncCLIDql:
    async def test_count(self, async_cli_models):
        await _create(async_cli_models, "async_dql_alice", 20)
        code, out, err = await run_cli_async(
            ["dql", "count", "--model", async_cli_models.model, "-o", "value"]
        )
        assert code == 0, err
        assert int(out.strip()) >= 1

    async def test_run_query_factory(self, async_cli_models):
        await _create(async_cli_models, "async_run_alice", 20)
        await _create(async_cli_models, "async_run_bob", 40)
        code, out, err = await run_cli_async(
            [
                "dql",
                "run",
                "--model",
                async_cli_models.model,
                "--query",
                async_cli_models.query,
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        rows = json.loads(out)
        assert rows and all(row["age"] >= 18 for row in rows)

