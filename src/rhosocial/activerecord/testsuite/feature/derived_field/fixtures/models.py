# src/rhosocial/activerecord/testsuite/feature/derived_field/fixtures/models.py
from typing import ClassVar, Optional

from typing_extensions import Annotated

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.base import DerivedField, FieldProxy
from rhosocial.activerecord.backend.expression import Column, Literal


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
