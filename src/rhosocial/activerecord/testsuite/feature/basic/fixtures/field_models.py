# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the basic tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""

from datetime import datetime
from typing import Optional, Type, Any, Dict, Set


from rhosocial.activerecord.base import DerivedField
from rhosocial.activerecord.base.fields import UseAdapter, UseColumn, UseSqlType
from rhosocial.activerecord.backend.expression import Literal as SQLLiteral, NumericColumn
from rhosocial.activerecord.backend.expression.types import TimestampType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy

# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.

try:
    from typing import Annotated, ClassVar
except ImportError:
    from typing_extensions import Annotated, ClassVar

from .annotations import SQL_INT_PK
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
        self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None
    ) -> Any:
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

    id: Annotated[Optional[int], SQL_INT_PK] = None
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
