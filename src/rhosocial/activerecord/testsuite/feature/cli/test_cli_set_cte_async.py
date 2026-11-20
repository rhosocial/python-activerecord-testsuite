# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_set_cte_async.py
"""CLI SetOperation and CTE contract tests (asynchronous)."""

import json

import pytest

from .utils import run_cli_async, supports_basic_cte, supports_set_operation


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
    async def test_set_union_and_run(self, async_cli_models):
        await _create(async_cli_models, "async_set_one", 20)
        await _create(async_cli_models, "async_set_two", 40)

        code, out, err = await run_cli_async(
            [
                "set",
                "union",
                "--left-model",
                async_cli_models.model,
                "--right-model",
                async_cli_models.model,
                "--left-where",
                "age=20",
                "--right-where",
                "age=40",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20, 40}

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

    async def test_set_union_all(self, async_cli_models):
        if not supports_set_operation(async_cli_models.module.User, "supports_union_all"):
            pytest.skip("dialect does not support UNION ALL")
        await _create(async_cli_models, "async_union_all_one", 20)
        await _create(async_cli_models, "async_union_all_two", 40)
        code, out, err = await run_cli_async(
            [
                "set",
                "union-all",
                "--left-model",
                async_cli_models.model,
                "--right-model",
                async_cli_models.model,
                "--left-where",
                "age=20",
                "--right-where",
                "age=40",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20, 40}

    async def test_set_intersect(self, async_cli_models):
        if not supports_set_operation(async_cli_models.module.User, "supports_intersect"):
            pytest.skip("dialect does not support INTERSECT")
        await _create(async_cli_models, "async_intersect_one", 20)
        await _create(async_cli_models, "async_intersect_two", 40)
        code, out, err = await run_cli_async(
            [
                "set",
                "intersect",
                "--left-model",
                async_cli_models.model,
                "--right-model",
                async_cli_models.model,
                "--left-where",
                "age=20",
                "--right-where",
                "age=20",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        # Overlapping arms yield the shared row; an empty INTERSECT would leave
        # the CLI with no row to infer output fields from.
        assert {row["age"] for row in json.loads(out)} == {20}

    async def test_set_except(self, async_cli_models):
        if not supports_set_operation(async_cli_models.module.User, "supports_except"):
            pytest.skip("dialect does not support EXCEPT")
        await _create(async_cli_models, "async_except_one", 20)
        await _create(async_cli_models, "async_except_two", 40)
        code, out, err = await run_cli_async(
            [
                "set",
                "except",
                "--left-model",
                async_cli_models.model,
                "--right-model",
                async_cli_models.model,
                "--left-where",
                "age=20",
                "--right-where",
                "age=40",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20}

    async def test_cte_run(self, async_cli_models):
        if not supports_basic_cte(async_cli_models.module.User):
            pytest.skip("dialect does not support basic CTEs")
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

