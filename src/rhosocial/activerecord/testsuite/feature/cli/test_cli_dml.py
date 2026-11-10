# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_dml.py
"""CLI DML contract tests (synchronous)."""

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


class TestCLIDml:
    def test_create_list_update_delete(self, cli_models):
        user = _create(cli_models, "cli_alice", 30)
        code, out, err = run_cli(
            ["dql", "list", "--model", cli_models.model, "--limit", "5", "-o", "json"]
        )
        assert code == 0, err
        assert any(row["id"] == user["id"] for row in json.loads(out))

        code, out, err = run_cli(
            [
                "dml",
                "update",
                "--model",
                cli_models.model,
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

        code, out, err = run_cli(
            [
                "dml",
                "delete",
                "--model",
                cli_models.model,
                "--pk",
                str(user["id"]),
                "--yes",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["action"] == "delete"

    def test_delete_requires_confirmation(self, cli_models):
        user = _create(cli_models, "cli_bob", 25)
        code, out, err = run_cli(
            [
                "dml",
                "delete",
                "--model",
                cli_models.model,
                "--pk",
                str(user["id"]),
                "-o",
                "json",
            ]
        )
        assert code != 0
        assert out == ""
        assert "--yes" in err
