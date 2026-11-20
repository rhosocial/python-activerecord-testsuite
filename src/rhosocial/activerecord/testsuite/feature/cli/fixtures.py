# src/rhosocial/activerecord/testsuite/feature/cli/fixtures.py
"""CLI-specific models that do not need new database schemas."""
from rhosocial.activerecord.field import IntegerPKMixin

try:  # Python 3.8 has no typing.Annotated
    from typing import Annotated, Optional
except ImportError:  # pragma: no cover - only on 3.8
    from typing import Optional

    from typing_extensions import Annotated

from rhosocial.activerecord.backend.expression.types import IntegerType, VarCharType
from rhosocial.activerecord.backend.migration import MigrationDirection, migration
from rhosocial.activerecord.base import UseSqlType
from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class CLIReadOnlyUser(IntegerPKMixin, ActiveRecord, ReadOnlyMixin):
    """Read-only view of the standard ``users`` table."""

    @classmethod
    def table_name(cls):
        return "users"

    id: Optional[int] = None
    username: str = ""


class AsyncCLIReadOnlyUser(IntegerPKMixin, AsyncActiveRecord, ReadOnlyMixin):
    """Async read-only view of the standard ``users`` table."""

    @classmethod
    def table_name(cls):
        return "users"

    id: Optional[int] = None
    username: str = ""


# Portable migration fixtures for the ``migrate`` CLI contract.  The functions
# live in a real importable module so their FQNs resolve through the CLI's
# resolver without registering a throw-away module in ``sys.modules``.
MIGRATE_PROBE_VERSION = "cli_m001_probe"
MIGRATE_CHILD_VERSION = "cli_m002_probe_child"
MIGRATE_DUP_VERSION = "cli_m900_duplicate"
MIGRATE_SYNC_ONLY_VERSION = "cli_m901_sync_only"


class CLIMigrateProbe(IntegerPKMixin, ActiveRecord):
    """First probe table built by the portable migrate CLI contract."""

    @classmethod
    def table_name(cls):
        return "cli_migrate_probe"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    name: Annotated[str, UseSqlType(VarCharType(length=64))]


class CLIMigrateProbeChild(IntegerPKMixin, ActiveRecord):
    """Second probe table, dependent on the first, for ordering checks."""

    @classmethod
    def table_name(cls):
        return "cli_migrate_probe_child"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    label: Annotated[str, UseSqlType(VarCharType(length=64))]


class AsyncCLIMigrateProbe(IntegerPKMixin, AsyncActiveRecord):
    """Async first probe table built by the portable migrate CLI contract."""

    @classmethod
    def table_name(cls):
        return "cli_migrate_probe"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    name: Annotated[str, UseSqlType(VarCharType(length=64))]


class AsyncCLIMigrateProbeChild(IntegerPKMixin, AsyncActiveRecord):
    """Async second probe table, dependent on the first, for ordering checks."""

    @classmethod
    def table_name(cls):
        return "cli_migrate_probe_child"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    label: Annotated[str, UseSqlType(VarCharType(length=64))]


@migration(MIGRATE_PROBE_VERSION)
def migrate_probe_create(ctx):
    if ctx.direction == MigrationDirection.UP:
        ctx.apply(CLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        ctx.apply(CLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_CHILD_VERSION, dependencies=(MIGRATE_PROBE_VERSION,))
def migrate_probe_child(ctx):
    if ctx.direction == MigrationDirection.UP:
        ctx.apply(CLIMigrateProbeChild.create_table_statement(backend=ctx.backend))
    else:
        ctx.apply(CLIMigrateProbeChild.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_DUP_VERSION)
def migrate_probe_dup_a(ctx):
    if ctx.direction == MigrationDirection.UP:
        ctx.apply(CLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        ctx.apply(CLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_DUP_VERSION)
def migrate_probe_dup_b(ctx):
    if ctx.direction == MigrationDirection.UP:
        ctx.apply(CLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        ctx.apply(CLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_SYNC_ONLY_VERSION)
def migrate_probe_sync_only(ctx):
    if ctx.direction == MigrationDirection.UP:
        ctx.apply(CLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        ctx.apply(CLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_PROBE_VERSION)
async def async_migrate_probe_create(ctx):
    if ctx.direction == MigrationDirection.UP:
        await ctx.apply(AsyncCLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        await ctx.apply(AsyncCLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_CHILD_VERSION, dependencies=(MIGRATE_PROBE_VERSION,))
async def async_migrate_probe_child(ctx):
    if ctx.direction == MigrationDirection.UP:
        await ctx.apply(AsyncCLIMigrateProbeChild.create_table_statement(backend=ctx.backend))
    else:
        await ctx.apply(
            AsyncCLIMigrateProbeChild.drop_table_statement(backend=ctx.backend, if_exists=True)
        )


@migration(MIGRATE_DUP_VERSION)
async def async_migrate_probe_dup_a(ctx):
    if ctx.direction == MigrationDirection.UP:
        await ctx.apply(AsyncCLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        await ctx.apply(AsyncCLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))


@migration(MIGRATE_DUP_VERSION)
async def async_migrate_probe_dup_b(ctx):
    if ctx.direction == MigrationDirection.UP:
        await ctx.apply(AsyncCLIMigrateProbe.create_table_statement(backend=ctx.backend))
    else:
        await ctx.apply(AsyncCLIMigrateProbe.drop_table_statement(backend=ctx.backend, if_exists=True))
