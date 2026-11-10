# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_set_cte_async.py
"""CLI SetOperation and CTE contract tests (asynchronous)."""

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


class TestAsyncCLISetCte:
    async def test_set_run(self, async_cli_models):
        await _create(async_cli_models, "async_set_one", 20)
        await _create(async_cli_models, "async_set_two", 40)
        code, out, err = await run_cli_async(
            [
                "set",
                "run",
                "--model",
                async_cli_models.model,
                "--query",
                async_cli_models.union_query,
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20, 40}

    async def test_cte_run(self, async_cli_models):
        await _create(async_cli_models, "async_cte_one", 20)
        await _create(async_cli_models, "async_cte_two", 40)
        code, out, err = await run_cli_async(
            [
                "cte",
                "run",
                "--model",
                async_cli_models.model,
                "--query",
                async_cli_models.cte_query,
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20, 40}

