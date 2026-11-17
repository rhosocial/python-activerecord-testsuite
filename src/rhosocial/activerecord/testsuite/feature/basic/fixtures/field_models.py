# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/field_models.py
"""Field-mapping and derived-field fixtures for the ``basic/fields`` group.

The group has one bare/annotated pair sharing a single table (``field_rows``):

* ``FieldRow`` / ``AsyncFieldRow`` write only Python type annotations.
* ``FieldRowAnnotated`` / ``AsyncFieldRowAnnotated`` add ``UseColumn`` renames,
  a ``UseAdapter`` value adaptation and a derived field.  None of those change
  the stored columns (README section 2 P2), so both models bind to the same
  table and the declaration tests compare their derived DDL for equality.

Identity is not a variant axis (F11): ``Optional[int]`` plus the framework's
``pk_auto_generated()`` default is the whole primary-key declaration on both
sides.  Sync and async twins share one mixin per variant (P4).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Set, Tuple, Type

from rhosocial.activerecord.backend.expression import Literal as SQLLiteral
from rhosocial.activerecord.backend.expression import NumericColumn
from rhosocial.activerecord.backend.expression.types import IntegerType, TimestampType
from rhosocial.activerecord.base import DerivedField
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import (
    UseAdapter,
    UseColumn,
    UseSqlType,
)
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.

try:
    from typing import Annotated, ClassVar
except ImportError:
    from typing_extensions import Annotated, ClassVar

from .operations import Operation, TableFixture
from .user_models import (
    ColumnMappingModel,
    MappedPost,
    MixedAnnotationModel,
)

# --- model bodies (moved from models.py) -------------------------------


class Product(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: NumericColumn(d, "price") * SQLLiteral(d, 0.9),
            ),
        ]
    ]

    total_value: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
            ),
        ]
    ]


class AsyncProduct(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: NumericColumn(d, "price") * SQLLiteral(d, 0.9),
            ),
        ]
    ]

    total_value: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
            ),
        ]
    ]


class ProductFormA(ActiveRecord):
    """Form A declaration: ClassVar[DerivedField] = DerivedField(...)."""

    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * SQLLiteral(d, 0.9),
    )

    total_value: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    )


class AsyncProductFormA(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * SQLLiteral(d, 0.9),
    )

    total_value: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    )


class PriceToIntAdapter:
    """Adapter that rounds float price to int for from_database."""

    def to_database(
        self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        return float(value)

    def from_database(
        self,
        value: Any,
        target_type: Type,
        options: Optional[Dict[str, Any]] = None,
        original_type: Any = None,
    ) -> Any:
        # ``original_type`` is the declared annotation (may be Optional[...]);
        # this adapter only needs the driver value.
        return int(round(value))

    @property
    def supported_types(self) -> Dict[Type, Set[Type]]:
        return {int: {float}}


class ProductWithProxy(ActiveRecord):
    """Product model using FieldProxy in DerivedField expressions."""

    @classmethod
    def table_name(cls):
        return "product"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: ProductWithProxy.c.price * SQLLiteral(d, 0.9),
            ),
        ]
    ]

    total_value: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: ProductWithProxy.c.price * ProductWithProxy.c.quantity,
            ),
        ]
    ]


class AsyncProductWithProxy(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: AsyncProductWithProxy.c.price * SQLLiteral(d, 0.9),
            ),
        ]
    ]

    total_value: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: AsyncProductWithProxy.c.price * AsyncProductWithProxy.c.quantity,
            ),
        ]
    ]


class ProductWithColumnAndAdapter(ActiveRecord):
    """Product model with UseColumn and UseAdapter on derived fields."""

    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: NumericColumn(d, "price") * SQLLiteral(d, 0.9),
            ),
            UseColumn("disc"),
        ]
    ]

    total_int: ClassVar[
        Annotated[
            int,
            DerivedField(
                lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
            ),
            UseAdapter(PriceToIntAdapter(), int),
        ]
    ]


class AsyncProductWithColumnAndAdapter(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[
        Annotated[
            float,
            DerivedField(
                lambda d: NumericColumn(d, "price") * SQLLiteral(d, 0.9),
            ),
            UseColumn("disc"),
        ]
    ]

    total_int: ClassVar[
        Annotated[
            int,
            DerivedField(
                lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
            ),
            UseAdapter(PriceToIntAdapter(), int),
        ]
    ]


# --- bare / annotated field variants (shared table) --------------------------


class FieldRowFields:
    """Bare fields: Python annotations only, zero ``Annotated`` markers."""

    id: Optional[int] = None
    label: str
    amount: Decimal
    count: int


class FieldRowAnnotatedFields:
    """Annotated fields: column renames, value adapter and a derived field.

    Only non-storage-changing markers appear here, so this model derives the
    very same ``field_rows`` table as :class:`FieldRowFields`.  ``title`` maps
    to the ``label`` column and ``total`` maps to ``count``; the adapter changes
    the Python value's representation, not the column's DDL type.
    """

    id: Optional[int] = None
    title: Annotated[str, UseColumn("label")]
    amount: Decimal
    total: Annotated[int, UseColumn("count"), UseAdapter(PriceToIntAdapter(), int)]

    discounted: ClassVar[
        Annotated[
            float,
            DerivedField(lambda d: NumericColumn(d, "amount") * SQLLiteral(d, 0.9)),
        ]
    ]


class FieldRow(FieldRowFields, ActiveRecord):
    """Bare field variant, bound to ``field_rows``."""

    @classmethod
    def table_name(cls):
        return "field_rows"


class AsyncFieldRow(FieldRowFields, AsyncActiveRecord):
    """Async twin of :class:`FieldRow` (P4: same fields, same table)."""

    @classmethod
    def table_name(cls):
        return "field_rows"


class FieldRowAnnotated(FieldRowAnnotatedFields, ActiveRecord):
    """Fully annotated field variant, bound to the same ``field_rows`` table."""

    @classmethod
    def table_name(cls):
        return "field_rows"


class AsyncFieldRowAnnotated(FieldRowAnnotatedFields, AsyncActiveRecord):
    """Async twin of :class:`FieldRowAnnotated` (P4)."""

    @classmethod
    def table_name(cls):
        return "field_rows"


# --- L1 fixture definitions ---------------------------------------------------
# A definition class receives only a ``dialect``: it builds the DDL expressions
# its model needs and knows nothing about backends, databases, or execution.
# Which definitions an environment uses, and in what order, is decided by the
# L2 fixtures in each test directory.
#
# The shared suite names only generic concepts; a backend name, or a
# backend-specific assumption, must never appear here.


class CommentDdl(ActiveRecord):
    """DDL source for ``comments``.

    ``MappedComment`` renames ``created_at`` to ``comment_creation_date`` for
    the mapping tests; binding both it and DefaultTimestampMixin into one DDL
    source would declare the column twice. The table itself is plain, so it
    gets its own source with no mapped timestamp field.
    """

    @classmethod
    def table_name(cls):
        return "comments"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    post_ref: int
    author: str
    text: str
    created_at: Annotated[datetime, UseSqlType(TimestampType(precision=3))]
    approved: bool = False
    updated_at: Annotated[datetime, UseSqlType(TimestampType(precision=3))]


_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))
FIELD_FIXTURES = (
    TableFixture(table="posts", source=MappedPost, operations=_OPS),
    TableFixture(table="comments", source=CommentDdl, operations=_OPS),
    TableFixture(table="column_mapping_items", source=ColumnMappingModel, operations=_OPS),
    TableFixture(table="mixed_annotation_items", source=MixedAnnotationModel, operations=_OPS),
    TableFixture(table="product", source=Product, operations=_OPS),
)

#: The bare/annotated pair shares one table; the annotations only rename
#: columns and adapt values (README section 2 P2), so one registration covers
#: both models.  Per-column operations name the switch a dialect must answer.
FIELD_VARIANT_COLUMN_SWITCHES = (
    ("id", "integer"),
    ("label", "varchar"),
    ("amount", "decimal"),
    ("count", "integer"),
)
FIELD_VARIANT_COLUMN_OPS = tuple(
    Operation("create_table", requires_on=(switch,), column=column)
    for column, switch in FIELD_VARIANT_COLUMN_SWITCHES
)
FIELD_VARIANT_FIXTURES: Tuple[TableFixture, ...] = (
    TableFixture(
        table="field_rows",
        source=FieldRow,
        operations=_OPS + FIELD_VARIANT_COLUMN_OPS,
    ),
)

__all__ = [
    "FIELD_FIXTURES",
    "FIELD_VARIANT_FIXTURES",
    "AsyncFieldRow",
    "AsyncFieldRowAnnotated",
    "AsyncProduct",
    "AsyncProductFormA",
    "AsyncProductWithColumnAndAdapter",
    "AsyncProductWithProxy",
    "CommentDdl",
    "FieldRow",
    "FieldRowAnnotated",
    "PriceToIntAdapter",
    "Product",
    "ProductFormA",
    "ProductWithColumnAndAdapter",
    "ProductWithProxy",
]
