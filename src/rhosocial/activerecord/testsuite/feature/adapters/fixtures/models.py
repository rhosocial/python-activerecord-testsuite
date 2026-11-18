# src/rhosocial/activerecord/testsuite/feature/adapters/fixtures/models.py
"""L1 fixture definitions for the shared neutral-type contract.

A fixture class holds the test ActiveRecord classes together with the
DDL/DML expression instances they need.  It receives only a ``dialect`` and
never a backend; composing and executing the environment belongs to the L2
fixtures.

Expression names are imported under short aliases so the definitions stay
readable.
"""
from rhosocial.activerecord.backend.expression.statements import auto_increment_parts  # noqa: E402
from rhosocial.activerecord.field import IntegerPKMixin

from typing import Optional

from pydantic import ConfigDict
from rhosocial.activerecord.backend.adapters.bitstring import BitString
from rhosocial.activerecord.backend.adapters.geometry import Geometry, Point
from rhosocial.activerecord.backend.adapters.network import MacAddress
from rhosocial.activerecord.backend.adapters.range import Multirange, Range
from rhosocial.activerecord.backend.adapters.vector import Vector
from rhosocial.activerecord.backend.expression import ColumnConstraint as Constraint
from rhosocial.activerecord.backend.expression import ColumnDefinition as Column
from rhosocial.activerecord.backend.expression import CreateTableStatement as CreateTable
from rhosocial.activerecord.backend.expression import DropTableStatement as DropTable
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
)
from rhosocial.activerecord.backend.expression.types import IntegerType as Int
from rhosocial.activerecord.backend.expression.types import TextType as Text
from rhosocial.activerecord.backend.expression.types import VarCharType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

# --- Generic column type concepts (local to this group) --------------------
#
# These helpers used to live in a cross-group type-helpers module.
# Each group that needs them now owns its own copy: the shared suite declares
# only generic concepts and lets the dialect render them, without consulting a
# backend name.

#: Bounded length for comparable text; ten such columns stay inside the
#: tightest row-width limit the suite meets (MySQL 65535 bytes at 4 B/char).
_SHORT_TEXT_LENGTH = 255


def _require_data_type(dialect, concept: str) -> None:
    """Skip when the dialect has not declared support for *concept*."""
    probe = getattr(dialect, "supports_data_types", None)
    if not callable(probe):
        return
    supported = probe() or {}
    if concept not in supported:
        import pytest

        pytest.skip(
            f"{getattr(dialect, 'name', 'this dialect')} does not support "
            f"the generic data type {concept!r}"
        )


def short_text(dialect):
    """Comparable text for identity-like columns (a bounded VARCHAR)."""
    _require_data_type(dialect, "varchar")
    return VarCharType(dialect, _SHORT_TEXT_LENGTH)


def long_text(dialect):
    """Unbounded text payload; never compared or sorted."""
    return Text(dialect)


def array_type(dialect, element_type):
    """Native ARRAY where the dialect renders it, else a text carrier."""
    probe = getattr(dialect, "supports_data_types", None)
    supported = probe() if callable(probe) else {}
    if "array" in supported:
        return ArrayType(dialect, element_type=element_type)
    return Text(dialect)


class NeutralTypes(IntegerPKMixin, ActiveRecord):
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


class AsyncNeutralTypes(IntegerPKMixin, AsyncActiveRecord):
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
    """Fixture class: model classes plus their DDL expression instances."""

    model = NeutralTypes
    async_model = AsyncNeutralTypes

    def __init__(self, name="id"):
        data_type, attributes = auto_increment_parts(self.dialect, Int(self.dialect))
        return Column(
            self.dialect, name, data_type,
            constraints=[Constraint(self.dialect, branch=PrimaryKey(self.dialect))],
            attributes=attributes,
        )

