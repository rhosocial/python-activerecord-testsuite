# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_set_cte.py
"""CLI SetOperation and CTE contract tests (synchronous)."""

import json

import pytest

from .utils import run_cli, supports_basic_cte, supports_set_operation


def _create(models, username, age):
    code, out, err = run_cli(
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


class TestCLISetCte:
    def test_set_union_and_run(self, cli_models):
        _create(cli_models, "set_one", 20)
        _create(cli_models, "set_two", 40)

        code, out, err = run_cli(
            [
                "set",
                "union",
                "--left-model",
                cli_models.model,
                "--right-model",
                cli_models.model,
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

        code, out, err = run_cli(
            [
                "set",
                "run",
                "--model",
                cli_models.model,
                "--query",
                cli_models.union_query,
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20, 40}

    def test_set_union_all(self, cli_models):
        if not supports_set_operation(cli_models.module.User, "supports_union_all"):
            pytest.skip("dialect does not support UNION ALL")
        _create(cli_models, "union_all_one", 20)
        _create(cli_models, "union_all_two", 40)
        code, out, err = run_cli(
            [
                "set",
                "union-all",
                "--left-model",
                cli_models.model,
                "--right-model",
                cli_models.model,
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

    def test_set_intersect(self, cli_models):
        if not supports_set_operation(cli_models.module.User, "supports_intersect"):
            pytest.skip("dialect does not support INTERSECT")
        _create(cli_models, "intersect_one", 20)
        _create(cli_models, "intersect_two", 40)
        code, out, err = run_cli(
            [
                "set",
                "intersect",
                "--left-model",
                cli_models.model,
                "--right-model",
                cli_models.model,
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

    def test_set_except(self, cli_models):
        if not supports_set_operation(cli_models.module.User, "supports_except"):
            pytest.skip("dialect does not support EXCEPT")
        _create(cli_models, "except_one", 20)
        _create(cli_models, "except_two", 40)
        code, out, err = run_cli(
            [
                "set",
                "except",
                "--left-model",
                cli_models.model,
                "--right-model",
                cli_models.model,
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

    def test_cte_run(self, cli_models):
        if not supports_basic_cte(cli_models.module.User):
            pytest.skip("dialect does not support basic CTEs")
        _create(cli_models, "cte_one", 20)
        _create(cli_models, "cte_two", 40)
        code, out, err = run_cli(
            [
                "cte",
                "run",
                "--model",
                cli_models.model,
                "--query",
                cli_models.cte_query,
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert {row["age"] for row in json.loads(out)} == {20, 40}
