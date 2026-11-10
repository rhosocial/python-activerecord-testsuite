# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_dql.py
"""CLI DQL contract tests (synchronous)."""

import json

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


class TestCLIDql:
    def test_count_and_exists(self, cli_models):
        _create(cli_models, "dql_alice", 20)
        _create(cli_models, "dql_bob", 40)
        code, out, err = run_cli(
            ["dql", "count", "--model", cli_models.model, "-o", "value"]
        )
        assert code == 0, err
        assert int(out.strip()) >= 2

        code, out, err = run_cli(
            [
                "dql",
                "exists",
                "--model",
                cli_models.model,
                "--where",
                "username=dql_alice",
                "-o",
                "value",
            ]
        )
        assert code == 0, err
        assert out.strip() == "true"

    def test_aggregate_group_by(self, cli_models):
        _create(cli_models, "agg_alice", 20)
        _create(cli_models, "agg_bob", 40)
        code, out, err = run_cli(
            [
                "dql",
                "aggregate",
                "--model",
                cli_models.model,
                "--fn",
                "count",
                "--field",
                "*",
                "--group-by",
                "age",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        rows = json.loads(out)
        assert rows and all("value" in row for row in rows)

    def test_run_query_factory(self, cli_models):
        _create(cli_models, "run_alice", 20)
        _create(cli_models, "run_bob", 40)
        code, out, err = run_cli(
            [
                "dql",
                "run",
                "--model",
                cli_models.model,
                "--query",
                cli_models.query,
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        rows = json.loads(out)
        assert rows and all(row["age"] >= 18 for row in rows)
