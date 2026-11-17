# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""Baseline aggregate for the basic fixtures.

Each table's model now lives in its group module (``user_models``,
``field_models``, ``type_rows_models``, ...); this file only re-exports them so
older importers of ``fixtures.models`` keep working. It declares no model of
its own: there is one definition site per table.
"""

from .composite_pk_models import (
    AsyncMappedOrderItem,
    AsyncOrder,
    AsyncOrderItem,
    AsyncStoreInventory,
    MappedOrderItem,
    Order,
    OrderItem,
    StoreInventory,
)  # noqa: F401
from .connection_models import AsyncTestUser, TestUser  # noqa: F401
from .field_models import (
    AsyncProduct,
    AsyncProductFormA,
    AsyncProductWithColumnAndAdapter,
    AsyncProductWithProxy,
    Product,
    ProductFormA,
    ProductWithColumnAndAdapter,
    ProductWithProxy,
)  # noqa: F401
from .type_adapter_models import (  # noqa: F401
    AsyncTypeAdapterTest,
    TypeAdapterTest,
    YesOrNoBooleanAdapter,
)
from .type_rows_models import (  # noqa: F401
    AsyncTypeCase,
    AsyncTypeTestModel,
    TypeCase,
    TypeTestModel,
)
from .user_models import (
    AsyncBulkUser,
    AsyncColumnMappingModel,
    AsyncMappedComment,
    AsyncMappedPost,
    AsyncMappedUser,
    AsyncMixedAnnotationModel,
    AsyncValidatedFieldUser,
    AsyncValidatedUser,
    AsyncUser,
    BulkUser,
    ColumnMappingModel,
    IntToStringAdapter,
    JsonToStringAdapter,
    ListToStringAdapter,
    MappedComment,
    MappedPost,
    MappedUser,
    MixedAnnotationModel,
    User,
    ValidatedFieldUser,
    ValidatedUser,
)  # noqa: F401
from .validation_models import (  # noqa: F401
    AsyncPydanticValidatedModel,
    PydanticValidatedFieldsMixin,
    PydanticValidatedModel,
)

__all__ = [
    "AsyncBulkUser",
    "AsyncColumnMappingModel",
    "AsyncMappedComment",
    "AsyncMappedOrderItem",
    "AsyncMappedPost",
    "AsyncMappedUser",
    "AsyncMixedAnnotationModel",
    "AsyncOrder",
    "AsyncOrderItem",
    "AsyncProduct",
    "AsyncProductFormA",
    "AsyncProductWithColumnAndAdapter",
    "AsyncProductWithProxy",
    "AsyncPydanticValidatedModel",
    "AsyncStoreInventory",
    "AsyncTestUser",
    "AsyncTypeAdapterTest",
    "AsyncTypeCase",
    "AsyncTypeTestModel",
    "AsyncUser",
    "AsyncValidatedFieldUser",
    "AsyncValidatedUser",
    "BulkUser",
    "ColumnMappingModel",
    "IntToStringAdapter",
    "JsonToStringAdapter",
    "ListToStringAdapter",
    "MappedComment",
    "MappedOrderItem",
    "MappedPost",
    "MappedUser",
    "MixedAnnotationModel",
    "Order",
    "OrderItem",
    "PydanticValidatedFieldsMixin",
    "PydanticValidatedModel",
    "Product",
    "ProductFormA",
    "ProductWithColumnAndAdapter",
    "ProductWithProxy",
    "StoreInventory",
    "TestUser",
    "TypeAdapterTest",
    "TypeCase",
    "TypeTestModel",
    "User",
    "ValidatedFieldUser",
    "ValidatedUser",
    "YesOrNoBooleanAdapter",
]
