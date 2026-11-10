# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_validation.py
"""CLI validation contract tests (synchronous)."""

import json

from .utils import run_cli


def _payload(username, age):
    return {"username": username, "email": f"{username}@example.com", "age": age}


def _create(models, payload):
    return run_cli(
        [
            "dml",
            "create",
            "--model",
            models.validated_model,
            "--data",
            json.dumps(payload),
            "-o",
            "json",
        ]
    )


class TestCLIValidation:
    def test_create_rejects_field_constraint(self, cli_models):
        code, out, err = _create(cli_models, _payload("ab", 20))
        assert code == 1
        assert out == ""
        assert "ValidatedUser" in err

    def test_create_rejects_business_rule(self, cli_models):
        code, out, err = _create(cli_models, _payload("youngcli", 12))
        assert code == 1
        assert out == ""
        assert "13" in err

    def test_update_keeps_row_when_validation_fails(self, cli_models):
        code, out, err = _create(cli_models, _payload("stablecli", 20))
        assert code == 0, err
        record_id = json.loads(out)["id"]

        code, out, err = run_cli(
            [
                "dml",
                "update",
                "--model",
                cli_models.validated_model,
                "--pk",
                str(record_id),
                "--data",
                json.dumps({"age": 160}),
                "-o",
                "json",
            ]
        )
        assert code == 1
        assert out == ""
        assert str(record_id) in err

        code, out, err = run_cli(
            [
                "dql",
                "get",
                "--model",
                cli_models.validated_model,
                "--pk",
                str(record_id),
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["age"] == 20

    def test_bulk_create_reports_item_index(self, cli_models):
        data = [
            _payload("bulkgood", 30),
            _payload("ab", 30),
        ]
        code, out, err = run_cli(
            [
                "dml",
                "bulk",
                "create",
                "--model",
                cli_models.validated_model,
                "--data",
                json.dumps(data),
                "-o",
                "json",
            ]
        )
        assert code == 1
        assert out == ""
        assert "item 2" in err

    def test_aggregate_rejects_unknown_field(self, cli_models):
        code, out, err = run_cli(
            [
                "dql",
                "aggregate",
                "--model",
                cli_models.validated_model,
                "--fn",
                "avg",
                "--field",
                "nope",
                "-o",
                "json",
            ]
        )
        assert code == 1
        assert out == ""
        assert 'Unknown aggregate field "nope"' in err

    def test_negative_limit_is_rejected(self, cli_models):
        code, out, err = run_cli(
            [
                "dql",
                "list",
                "--model",
                cli_models.validated_model,
                "--limit",
                "-1",
            ]
        )
        assert code == 1
        assert out == ""
        assert "--limit must be greater than or equal to 0" in err
