# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/types_complex_models.py
"""Complex-type bare / annotated fixture pair (``types_complex`` group).

The two tables answer two different questions:

* ``complex_rows`` (bare) asks what the framework stores when a field says
  nothing but its Python type.  Per README section 5 the common families
  (``UUID``, ``dict``, ``list``, ``timedelta``, ``Enum``, ``bytes``) and the
  parameterless business classes (``MacAddress``, ``Point``) are allowed to
  appear bare: their storage is decided by the class, not by a column option.
* ``complex_rows_annotated`` asks what an explicit declaration changes.  Each
  common column carries the annotation named in section 5; the dimensional
  families (``Vector``, ``Range``, ``BitString``) and XML appear only here,
  because their size / element / bit width is a column property and there is
  no Python type from which XML could be inferred.

Sync/async twins share their field declarations through plain mixins (P4),
so a one-sided drift shows up as a DDL mismatch.  No ``IdentityAttribute`` is
written: ``Optional[int]`` plus the framework's ``pk_auto_generated()``
default is the whole identity declaration (F11).
"""

import enum
import uuid
from datetime import timedelta
from typing import Optional, Tuple

from rhosocial.activerecord.backend.adapters import (
    BitString,
    MacAddress,
    Point,
    Range,
    Vector,
)
from rhosocial.activerecord.backend.adapters.network import MacAddressAdapterBase
from rhosocial.activerecord.backend.expression import BinaryColumn, XMLColumn
from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
    CustomType,
    EnumType,
    IntegerType,
    IntervalType,
    JsonType,
    TextType,
    VarCharType,
    XmlType,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import (
    UseAdapter,
    UseColumnType,
    UseComment,
    UseIndex,
    UseSqlType,
)
from rhosocial.activerecord.field import IntegerPKMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

from .operations import Operation, TableFixture

try:
    from typing import Annotated, ClassVar
except ImportError:  # Python 3.8
    from typing_extensions import Annotated, ClassVar


class ComplexKind(enum.Enum):
    """A small enumeration whose labels are the annotated ``EnumType`` values."""

    ALPHA = "alpha"
    BETA = "beta"


class CanonicalMacAddressAdapter(MacAddressAdapterBase):
    """Backend-neutral MAC adapter: canonical colon-separated text.

    The annotated variant pins the adapter (README section 5); the shared
    suite cannot import a backend's adapter, so this one uses the canonical
    string form that every backend's text/blob column can carry.
    """

    def __init__(self):
        super().__init__()
        self.register_type(MacAddress, str)

    def _encode(self, mac, target_type, options):
        return str(mac)

    def _decode(self, value, options):
        return MacAddress.parse(self._require_text(value))


# --- bare variants: Python types only -------------------------------------


class ComplexFields:
    """The one field declaration for the bare ``complex_rows`` table."""

    id: Optional[int] = None
    token: uuid.UUID
    payload: dict
    tags: list
    # A duration is still a timedelta (``field_python_type`` unwraps the
    # Optional); it is nullable because the shared suite cannot bind a bare
    # timedelta on every backend's DML driver without an explicit adapter.
    elapsed: Optional[timedelta] = None
    kind: ComplexKind
    raw: bytes
    nic: MacAddress
    location: Point


# --- annotated variants: section 5 annotations ----------------------------


class ComplexAnnotatedFields:
    """The one field declaration for ``complex_rows_annotated``.

    Every annotation is a *declaration*, not a guess: the storage types that
    are hard errors on some dialects (``ArrayType``, ``EnumType``, ``XmlType``)
    carry a portable fallback as a second candidate, so the annotated table
    can still be created where the native concept has no renderer.
    """

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    token: Annotated[uuid.UUID, UseIndex("ix_complex_rows_annotated_token")]
    payload: Annotated[dict, UseComment("complex JSON payload (<= 4000 bytes on Oracle)")]
    tags: Annotated[
        list,
        UseSqlType(ArrayType(element_type=VarCharType(length=32)), JsonType()),
    ]
    elapsed: Annotated[Optional[timedelta], UseSqlType(IntervalType())] = None
    kind: Annotated[
        ComplexKind,
        UseSqlType(EnumType(values=["alpha", "beta"]), VarCharType(length=32)),
    ]
    raw: Annotated[bytes, UseColumnType(BinaryColumn)]
    nic: Annotated[MacAddress, UseAdapter(CanonicalMacAddressAdapter(), str)]

    # Core has no geometry DataType and a backend-specific subtype cannot be
    # named in a shared fixture (R1); CustomType is the portable spelling of
    # the generic GEOMETRY subtype.  A native POINT(n)/SRID declaration belongs
    # in each backend's own contract tests.
    location: Annotated[Point, UseSqlType(CustomType(raw="GEOMETRY"))]

    # Dimensional families and XML: annotated only.  Their width/element/bit
    # count is a column property, and XML has no Python type to infer from.
    # Portable carriers are used here; the native semantics (dimension,
    # element type, bit width) need a backend-specific UseSqlType/UseColumnType
    # pair and are exercised in the backends' own suites.
    heading: Annotated[Optional[Vector], UseSqlType(JsonType())] = None
    span: Annotated[Optional[Range], UseSqlType(TextType())] = None
    bits: Annotated[Optional[BitString], UseSqlType(TextType())] = None
    markup: Annotated[
        Optional[str],
        UseSqlType(XmlType(), TextType()),
        UseColumnType(XMLColumn),
    ] = None


class ComplexRow(ComplexFields, IntegerPKMixin, ActiveRecord):
    """Bare sync model for ``complex_rows``."""

    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "complex_rows"


class AsyncComplexRow(ComplexFields, IntegerPKMixin, AsyncActiveRecord):
    """Bare async twin of :class:`ComplexRow`."""

    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "complex_rows"


class ComplexRowAnnotated(ComplexAnnotatedFields, IntegerPKMixin, ActiveRecord):
    """Fully annotated sync model for ``complex_rows_annotated``."""

    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "complex_rows_annotated"


class AsyncComplexRowAnnotated(ComplexAnnotatedFields, IntegerPKMixin, AsyncActiveRecord):
    """Fully annotated async twin of :class:`ComplexRowAnnotated`."""

    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "complex_rows_annotated"


def _column_operations(**switches) -> tuple:
    """One ``create_table`` operation per column, so a skip can name it."""
    return tuple(
        Operation("create_table", requires_on=concepts, column=column)
        for column, concepts in switches.items()
    )


_BARE_OPERATIONS = _column_operations(
    id=("integer",),
    token=("uuid",),
    payload=("json",),
    tags=("array",),
    elapsed=("interval",),
    kind=("enum",),
    raw=("blob",),
    nic=("mac",),
    location=("geometry",),
)

_ANNOTATED_OPERATIONS = _BARE_OPERATIONS + _column_operations(
    heading=("vector",),
    markup=("xml",),
)

COMPLEX_FIXTURES: Tuple[TableFixture, ...] = (
    TableFixture(
        table="complex_rows",
        source=ComplexRow,
        operations=_BARE_OPERATIONS + (Operation("insert"), Operation("drop_table")),
    ),
    TableFixture(
        table="complex_rows_annotated",
        source=ComplexRowAnnotated,
        operations=_ANNOTATED_OPERATIONS + (Operation("insert"), Operation("drop_table")),
    ),
)

__all__ = [
    "COMPLEX_FIXTURES",
    "ComplexAnnotatedFields",
    "ComplexFields",
    "ComplexKind",
    "ComplexRow",
    "ComplexRowAnnotated",
    "AsyncComplexRow",
    "AsyncComplexRowAnnotated",
    "CanonicalMacAddressAdapter",
]
