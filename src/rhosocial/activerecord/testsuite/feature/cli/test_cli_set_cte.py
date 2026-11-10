# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_set_cte.py
"""CLI SetOperation and CTE contract tests (synchronous)."""

import json

from rhosocial.activerecord.backend.dialect.protocols import CTESupport
from rhosocial.activerecord.testsuite.utils import requires_protocol

from .utils import run_cli


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

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_cte_run(self, cli_models):
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
