# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_bulk.py
"""CLI bulk DML contract tests (synchronous)."""

import json

from .utils import run_cli


class TestCLIBulk:
    def test_bulk_create_update_delete(self, cli_models):
        code, out, err = run_cli(
            [
                "dml",
                "bulk",
                "create",
                "--model",
                cli_models.bulk_model,
                "--data",
                '[{"name": "bulk_one", "age": 20},'
                '{"name": "bulk_two", "age": 30}]',
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        rows = json.loads(out)
        assert {row["name"] for row in rows} == {"bulk_one", "bulk_two"}
        ids = [row["id"] for row in rows]

        code, out, err = run_cli(
            [
                "dml",
                "bulk",
                "update",
                "--model",
                cli_models.bulk_model,
                "--data",
                json.dumps([{"id": ids[0], "age": 21}, {"id": ids[1], "age": 31}]),
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["affected"] == 2

        code, out, err = run_cli(
            [
                "dml",
                "bulk",
                "delete",
                "--model",
                cli_models.bulk_model,
                "--data",
                json.dumps(ids),
                "--yes",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["affected"] == 2
