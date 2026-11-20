# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/types_long_content_models.py
"""Declarations for the ``types_long_content`` fixture group (annotated only).

A bare twin is deliberately absent: an unannotated ``str`` is inferred as a short
VARCHAR and cannot hold the 16 000-character value this group writes, so a bare
variant would only prove that a column truncates (README §6).

``length`` on ``TextType`` / ``BlobType`` is a *minimum*, not a width: the dialect
rounds up to a tier of its own (MySQL TEXT/MEDIUMTEXT, Oracle CLOB,
SQL Server NVARCHAR(MAX), ...). 16 000 BMP characters stay inside MySQL TEXT.
``JsonType`` / ``XmlType`` carry no length yet; their payloads stay below
Oracle's 4 000-byte ``VARCHAR2`` ceiling, so this group asks only that the
concept be available, not that it hold an arbitrarily large document.
"""

from typing import Optional, Tuple

try:
    from typing import Annotated, ClassVar
except ImportError:  # pragma: no cover - Python 3.8 fallback
    from typing_extensions import Annotated, ClassVar

from rhosocial.activerecord.backend.expression.types import (
    BlobType,
    JsonType,
    TextType,
    XmlType,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import UseSqlType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

from .operations import Operation, TableFixture

__all__ = [
    "AsyncLongRow",
    "DOCUMENT_VALUE",
    "LONG_BYTES",
    "LONG_CONTENT_FIXTURES",
    "LONG_TEXT",
    "MARKUP_VALUE",
    "LongRow",
]

#: 16 000 BMP characters (3 bytes each in UTF-8 -> ~48 KB, inside MySQL TEXT).
LONG_TEXT = "数据" * 8000

#: 16 000 bytes, exactly the declared ``BlobType`` minimum.
LONG_BYTES = bytes(index % 256 for index in range(16000))

#: Kept under 4 000 bytes so Oracle's ``JsonType`` (VARCHAR2(4000)) can hold it.
DOCUMENT_VALUE = {"title": "长文档", "payload": "x" * 3300}

#: Kept under 4 000 bytes for the same reason, and is well-formed XML.
MARKUP_VALUE = "<root>" + ("x" * 3300) + "</root>"


class LongRowFields:
    """The single field declaration shared by the sync/async twins (P4).

    ``id`` is a plain ``Optional[int]``: the framework's default
    ``pk_auto_generated()`` derives the backend's own integer-key mechanism, so
    no mechanism attribute (``IdentityAttribute``) belongs in a shared fixture.
    """

    id: Optional[int] = None
    body: Annotated[str, UseSqlType(TextType(length=16000))]
    raw: Annotated[bytes, UseSqlType(BlobType(length=16000))]
    document: Annotated[dict, UseSqlType(JsonType())]
    markup: Annotated[str, UseSqlType(XmlType())]


class LongRow(LongRowFields, ActiveRecord):
    """Synchronous source for the ``long_rows`` table."""

    @classmethod
    def table_name(cls):
        return "long_rows"

    c: ClassVar[FieldProxy] = FieldProxy()


class AsyncLongRow(LongRowFields, AsyncActiveRecord):
    """Asynchronous twin of :class:`LongRow`; same fields, same table."""

    @classmethod
    def table_name(cls):
        return "long_rows"

    c: ClassVar[FieldProxy] = FieldProxy()


# Column-specific operations come first: ``table_reason`` returns the first
# refusal, and naming the column makes the skip reason actionable. The capacity
# prerequisite is carried by the model's ``length=16000`` declaration -- a
# dialect that answers the concept with that length-aware formatter rounds up
# to a tier that holds the value, so no separate capacity switch is invented.
_LONG_CONTENT_OPERATIONS = (
    Operation("insert", column="body", requires_on=("text",)),
    Operation("insert", column="raw", requires_on=("blob",)),
    Operation("insert", column="document", requires_on=("json",)),
    Operation("insert", column="markup", requires_on=("xml",)),
    Operation("create_table"),
    Operation("drop_table"),
)

LONG_CONTENT_FIXTURES: Tuple[TableFixture, ...] = (
    TableFixture(
        table="long_rows",
        source=LongRow,
        operations=_LONG_CONTENT_OPERATIONS,
    ),
)
