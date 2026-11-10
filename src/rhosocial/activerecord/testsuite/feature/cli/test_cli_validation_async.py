# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_validation_async.py
"""CLI validation contract tests (asynchronous)."""

import json

from .utils import run_cli_async


def _payload(username, age):
    return {"username": username, "email": f"{username}@example.com", "age": age}


async def _create(models, payload):
    return await run_cli_async(
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


class TestAsyncCLIValidation:
    async def test_create_rejects_field_constraint(self, async_cli_models):
        code, out, err = await _create(async_cli_models, _payload("ab", 20))
        assert code == 1
        assert out == ""
        assert "ValidatedUser" in err

    async def test_create_rejects_business_rule(self, async_cli_models):
        code, out, err = await _create(async_cli_models, _payload("youngcli", 12))
        assert code == 1
        assert out == ""
        assert "13" in err

    async def test_update_keeps_row_when_validation_fails(self, async_cli_models):
        code, out, err = await _create(async_cli_models, _payload("stablecli", 20))
        assert code == 0, err
        record_id = json.loads(out)["id"]

        code, out, err = await run_cli_async(
            [
                "dml",
                "update",
                "--model",
                async_cli_models.validated_model,
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

        code, out, err = await run_cli_async(
            [
                "dql",
                "get",
                "--model",
                async_cli_models.validated_model,
                "--pk",
                str(record_id),
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        assert json.loads(out)["age"] == 20

    async def test_bulk_create_reports_item_index(self, async_cli_models):
        data = [
            _payload("bulkgood", 30),
            _payload("ab", 30),
        ]
        code, out, err = await run_cli_async(
            [
                "dml",
                "bulk",
                "create",
                "--model",
                async_cli_models.validated_model,
                "--data",
                json.dumps(data),
                "-o",
                "json",
            ]
        )
        assert code == 1
        assert out == ""
        assert "item 2" in err

    async def test_aggregate_rejects_unknown_field(self, async_cli_models):
        code, out, err = await run_cli_async(
            [
                "dql",
                "aggregate",
                "--model",
                async_cli_models.validated_model,
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

    async def test_negative_limit_is_rejected(self, async_cli_models):
        code, out, err = await run_cli_async(
            [
                "dql",
                "list",
                "--model",
                async_cli_models.validated_model,
                "--limit",
                "-1",
            ]
        )
        assert code == 1
        assert out == ""
        assert "--limit must be greater than or equal to 0" in err
