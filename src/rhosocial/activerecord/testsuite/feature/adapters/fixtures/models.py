# src/rhosocial/activerecord/testsuite/feature/adapters/fixtures/models.py
"""L1 fixture definitions for the shared neutral-type contract.

A definition class holds the test ActiveRecord classes together with the
DDL/DML expression instances they need.  It receives only a ``dialect`` and
never a backend; composing and executing the environment belongs to the L2
fixtures.

Expression names are imported under short aliases so the definitions stay
readable.
"""
from typing import Optional

from pydantic import ConfigDict

from rhosocial.activerecord.backend.adapters.bitstring import BitString
from rhosocial.activerecord.backend.adapters.geometry import Geometry, Point
from rhosocial.activerecord.backend.adapters.network import MacAddress
from rhosocial.activerecord.backend.adapters.range import Multirange, Range
from rhosocial.activerecord.backend.adapters.vector import Vector
from rhosocial.activerecord.backend.expression import (
    ColumnConstraint as Constraint,
    ColumnDefinition as Column,
    CreateTableStatement as CreateTable,
    DropTableStatement as DropTable,
)
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.expression.types import (
    IntegerType as Int,
    TextType as Text,
)
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.testsuite.core.fixture_types import (
    array_type,
    long_text,
    short_text,
)


class NeutralTypes(ActiveRecord):
    """One row per neutral family; columns are generic text/array carriers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def table_name(cls) -> str:
        return "neutral_types"

    id: Optional[int] = None
    shape: Optional[Geometry] = None
    point: Optional[Point] = None
    vector: Optional[Vector] = None
    flags: Optional[BitString] = None
    window: Optional[Range] = None
    windows: Optional[Multirange] = None
    address: Optional[MacAddress] = None
    payload: Optional[dict] = None
    tags: Optional[list] = None


class AsyncNeutralTypes(AsyncActiveRecord):
    """Async twin of :class:`NeutralTypes`."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def table_name(cls) -> str:
        return "neutral_types"

    id: Optional[int] = None
    shape: Optional[Geometry] = None
    point: Optional[Point] = None
    vector: Optional[Vector] = None
    flags: Optional[BitString] = None
    window: Optional[Range] = None
    windows: Optional[Multirange] = None
    address: Optional[MacAddress] = None
    payload: Optional[dict] = None
    tags: Optional[list] = None


class NeutralTypesFixture:
    """Definition class: model classes plus their DDL expression instances."""

    model = NeutralTypes
    async_model = AsyncNeutralTypes

    def __init__(self, dialect):
        self.dialect = dialect
        self.create_table = CreateTable(
            dialect,
            table=Table(dialect, "neutral_types"),
            columns=[
                Column(
                    dialect,
                    "id",
                    Int(dialect),
                    constraints=[
                        Constraint(
                            dialect,
                            branch=PrimaryKey(dialect, is_auto_increment=True),
                        )
                    ],
                ),
                Column(dialect, "shape", long_text(dialect)),
                Column(dialect, "point", long_text(dialect)),
                Column(dialect, "vector", long_text(dialect)),
                Column(dialect, "window", long_text(dialect)),
                Column(dialect, "windows", long_text(dialect)),
                Column(dialect, "payload", long_text(dialect)),
                Column(dialect, "flags", short_text(dialect)),
                Column(dialect, "address", short_text(dialect)),
                Column(dialect, "tags", array_type(dialect, Text(dialect))),
            ],
        )
        self.drop_table = DropTable(
            dialect, table=Table(dialect, "neutral_types")
        )
