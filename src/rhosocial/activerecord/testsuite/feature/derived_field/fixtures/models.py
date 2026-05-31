# src/rhosocial/activerecord/testsuite/feature/derived_field/fixtures/models.py
from typing import Any, ClassVar, Dict, Optional, Set, Type

from typing_extensions import Annotated

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.base import DerivedField, FieldProxy, UseColumn, UseAdapter
from rhosocial.activerecord.backend.expression import Column, Literal
from rhosocial.activerecord.backend.type_adapter import SQLTypeAdapter


class Product(ActiveRecord):
    __table_name__ = "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: Column(d, "price") * Literal(d, 0.9),
        default_included=True,
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: Column(d, "price") * Column(d, "quantity"),
    )]]


class ProductFormA(ActiveRecord):
    """Product model using Form A declaration (ClassVar assignment)."""
    __table_name__ = "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[DerivedField] = DerivedField(
        lambda d: Column(d, "price") * Literal(d, 0.9),
        default_included=True,
    )

    total_value: ClassVar[DerivedField] = DerivedField(
        lambda d: Column(d, "price") * Column(d, "quantity"),
    )


class AsyncProduct(AsyncActiveRecord):
    __table_name__ = "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: Column(d, "price") * Literal(d, 0.9),
        default_included=True,
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: Column(d, "price") * Column(d, "quantity"),
    )]]


class ProductWithProxy(ActiveRecord):
    """Product model using FieldProxy in DerivedField expressions."""
    __table_name__ = "product"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: ProductWithProxy.c.price * Literal(d, 0.9),
        default_included=True,
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: ProductWithProxy.c.price * ProductWithProxy.c.quantity,
    )]]


class PriceToIntAdapter:
    """Adapter that rounds float price to int."""

    def to_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Any:
        return float(value)

    def from_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Any:
        return int(round(value))

    @property
    def supported_types(self) -> Dict[Type, Set[Type]]:
        return {int: {float}}


class ProductWithColumnAndAdapter(ActiveRecord):
    """Product model with UseColumn and UseAdapter on derived fields."""
    __table_name__ = "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    # UseColumn: SELECT alias is "disc" but Python attr is "discounted_price"
    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: Column(d, "price") * Literal(d, 0.9),
        default_included=True,
    ), UseColumn("disc")]]

    # UseAdapter: rounds the float result to int
    total_int: ClassVar[Annotated[int, DerivedField(
        lambda d: Column(d, "price") * Column(d, "quantity"),
    ), UseAdapter(PriceToIntAdapter(), int)]]


class AsyncProductWithProxy(AsyncActiveRecord):
    """Async product model using FieldProxy in DerivedField expressions."""
    __table_name__ = "product"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: AsyncProductWithProxy.c.price * Literal(d, 0.9),
        default_included=True,
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: AsyncProductWithProxy.c.price * AsyncProductWithProxy.c.quantity,
    )]]


class AsyncProductWithColumnAndAdapter(AsyncActiveRecord):
    """Async product model with UseColumn and UseAdapter on derived fields."""
    __table_name__ = "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: Column(d, "price") * Literal(d, 0.9),
        default_included=True,
    ), UseColumn("disc")]]

    total_int: ClassVar[Annotated[int, DerivedField(
        lambda d: Column(d, "price") * Column(d, "quantity"),
    ), UseAdapter(PriceToIntAdapter(), int)]]
