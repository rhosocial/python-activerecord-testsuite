# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_read_only.py
"""CLI read-only model contract tests (synchronous)."""

from .utils import run_cli


class TestCLIReadOnly:
    def test_dml_rejected(self, cli_models):
        code, out, err = run_cli(
            [
                "dml",
                "create",
                "--model",
                cli_models.read_only_model,
                "--data",
                '{"id": 1, "username": "nope"}',
                "-o",
                "json",
            ]
        )
        assert code == 6
        assert out == ""
        assert "read-only" in err

    def test_dql_still_works(self, cli_models):
        code, out, err = run_cli(
            ["dql", "count", "--model", cli_models.read_only_model, "-o", "value"]
        )
        assert code == 0, err
        assert int(out.strip()) >= 0
