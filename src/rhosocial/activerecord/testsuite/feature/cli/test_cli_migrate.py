# src/rhosocial/activerecord/testsuite/feature/cli/test_cli_migrate.py
"""Portable contract for the ``migrate`` CLI command group (synchronous).

The dialect-independent surface -- list, plan, validation and dry run -- is
covered everywhere. A real apply/rollback case is gated on the backend's
transactional-DDL capability.
"""

import json

import pytest

from .utils import run_cli

FIXTURE_MODULE = "rhosocial.activerecord.testsuite.feature.cli.fixtures"


def _migrate_fqn(name):
    """Build the fully qualified name of a migration fixture function."""
    return f"{FIXTURE_MODULE}:{name}"


def _supports_transactional_migrations(models):
    """Whether the configured backend can apply and roll back DDL in a transaction."""
    try:
        model = getattr(models.module, "User")
        backend = model.backend()
        dialect = getattr(backend, "dialect", None)
        supports = getattr(dialect, "supports_transactional_ddl", lambda: True)()
        manager = getattr(backend, "transaction_manager", None)
        return bool(supports) and hasattr(manager, "begin")
    except Exception:
        return False


class TestCLIMigrateContract:
    """The synchronous ``migrate`` CLI group contract."""

    def test_list_json_reports_versions_dependencies_and_kinds(self):
        """--list emits JSON with ordered versions, dependencies and kinds."""
        code, out, err = run_cli(
            [
                "migrate",
                _migrate_fqn("migrate_probe_create"),
                _migrate_fqn("migrate_probe_child"),
                "-o",
                "json",
                "--list",
            ]
        )
        assert code == 0, err
        payload = json.loads(out)
        assert payload["command"] == "migrate"
        assert payload["mode"] == "list"
        assert [row["version"] for row in payload["functions"]] == [
            "cli_m001_probe",
            "cli_m002_probe_child",
        ]
        assert payload["functions"][0]["kind"] == "sync"
        assert payload["functions"][1]["dependencies"] == ["cli_m001_probe"]

    def test_plan_json_reverses_order_for_down(self):
        """--plan shows the direction and reverses the order for down migrations."""
        code, out, err = run_cli(
            [
                "migrate",
                _migrate_fqn("migrate_probe_create"),
                _migrate_fqn("migrate_probe_child"),
                "--plan",
                "--direction",
                "down",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        payload = json.loads(out)
        assert payload["mode"] == "plan"
        assert payload["direction"] == "down"
        assert [row["version"] for row in payload["order"]] == [
            "cli_m002_probe_child",
            "cli_m001_probe",
        ]

    def test_list_text_stops_before_connecting(self):
        """Text --list renders versions and dependencies without a connection."""
        code, out, err = run_cli(
            [
                "migrate",
                _migrate_fqn("migrate_probe_create"),
                _migrate_fqn("migrate_probe_child"),
                "--list",
            ]
        )
        assert code == 0, err
        assert "Migration functions:" in out
        assert "cli_m001_probe" in out
        assert "cli_m002_probe_child" in out
        assert "dependencies: cli_m001_probe" in out

    def test_missing_async_variant_exits_with_state_code(self):
        """--async on a sync function without an async_variant exits with code 7."""
        code, out, err = run_cli(
            [
                "migrate",
                _migrate_fqn("migrate_probe_sync_only"),
                "--async",
            ]
        )
        assert code == 7
        assert "async_variant" in out + err

    def test_duplicate_version_exits_with_state_code(self, cli_models):
        """Two functions sharing one version are rejected with exit code 7."""
        code, out, err = run_cli(
            [
                "migrate",
                _migrate_fqn("migrate_probe_dup_a"),
                _migrate_fqn("migrate_probe_dup_b"),
                "--model",
                cli_models.model,
                "--dry-run",
            ]
        )
        assert code == 7
        assert "Duplicate migration version" in out + err

    def test_dry_run_json_renders_statements_without_writing(self, cli_models):
        """--dry-run emits a JSON payload with rendered SQL and writes nothing."""
        code, out, err = run_cli(
            [
                "migrate",
                _migrate_fqn("migrate_probe_create"),
                _migrate_fqn("migrate_probe_child"),
                "--model",
                cli_models.model,
                "--dry-run",
                "-o",
                "json",
            ]
        )
        assert code == 0, err
        payload = json.loads(out)
        assert payload["command"] == "migrate"
        assert payload["success"] is True
        assert payload["dry_run"] is True
        assert payload["versions"] == ["cli_m001_probe", "cli_m002_probe_child"]
        assert payload["dry_run_total"] == 2
        statements = payload["statements"]
        assert len(statements) == 2
        assert "CREATE TABLE" in statements[0]["sql"].upper()
        assert "cli_migrate_probe" in statements[0]["sql"]

    def test_apply_and_rollback_on_transactional_backends(self, cli_models):
        """A real apply then rollback runs only where transactional DDL exists."""
        if not _supports_transactional_migrations(cli_models):
            pytest.skip("backend cannot apply and roll back DDL in a transaction")
        argv = [
            "migrate",
            _migrate_fqn("migrate_probe_create"),
            "--model",
            cli_models.model,
        ]
        try:
            code, out, err = run_cli(argv)
            assert code == 0, err
            assert "cli_m001_probe" in out
        finally:
            down_code, down_out, down_err = run_cli(argv + ["--direction", "down"])
            assert down_code == 0, down_err
            assert "cli_m001_probe" in down_out
