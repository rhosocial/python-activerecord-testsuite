# src/rhosocial/activerecord/testsuite/feature/basic/conftest.py
"""Fixtures shared by the basic topic.

Each fixture names its model directly; the testsuite environment configures it
against the directory's database.  Which versioned model file supplies the
class is decided here, so tests only see fixture names.
"""
import pytest

from .fixtures import resolve

User = resolve("User")
AsyncUser = resolve("AsyncUser")
TypeCase = resolve("TypeCase")
AsyncTypeCase = resolve("AsyncTypeCase")
TypeTestModel = resolve("TypeTestModel")
AsyncTypeTestModel = resolve("AsyncTypeTestModel")
ValidatedUser = resolve("ValidatedFieldUser")
AsyncValidatedUser = resolve("AsyncValidatedFieldUser")
ValidatedProfile = resolve("ValidatedUser")
AsyncValidatedProfile = resolve("AsyncValidatedUser")
PydanticValidatedModel = resolve("PydanticValidatedModel")
AsyncPydanticValidatedModel = resolve("AsyncPydanticValidatedModel")
TypeAdapterTest = resolve("TypeAdapterTest")
AsyncTypeAdapterTest = resolve("AsyncTypeAdapterTest")
MappedUser = resolve("MappedUser")
AsyncMappedUser = resolve("AsyncMappedUser")
MappedPost = resolve("MappedPost")
AsyncMappedPost = resolve("AsyncMappedPost")
MappedComment = resolve("MappedComment")
AsyncMappedComment = resolve("AsyncMappedComment")
ColumnMappingModel = resolve("ColumnMappingModel")
AsyncColumnMappingModel = resolve("AsyncColumnMappingModel")
MixedAnnotationModel = resolve("MixedAnnotationModel")
AsyncMixedAnnotationModel = resolve("AsyncMixedAnnotationModel")
BulkUser = resolve("BulkUser")
AsyncBulkUser = resolve("AsyncBulkUser")
OrderItem = resolve("OrderItem")
AsyncOrderItem = resolve("AsyncOrderItem")
Order = resolve("Order")
AsyncOrder = resolve("AsyncOrder")
MappedOrderItem = resolve("MappedOrderItem")
AsyncMappedOrderItem = resolve("AsyncMappedOrderItem")
Product = resolve("Product")
AsyncProduct = resolve("AsyncProduct")
ProductFormA = resolve("ProductFormA")
AsyncProductFormA = resolve("AsyncProductFormA")
ProductWithProxy = resolve("ProductWithProxy")
AsyncProductWithProxy = resolve("AsyncProductWithProxy")
ProductWithColumnAndAdapter = resolve("ProductWithColumnAndAdapter")
AsyncProductWithColumnAndAdapter = resolve("AsyncProductWithColumnAndAdapter")


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


def _disconnect_models(models) -> None:
    for model in models:
        _disconnect(model)


async def _disconnect_models_async(models) -> None:
    for model in models:
        await _disconnect_async(model)


@pytest.fixture(name="user_class")
def user_class(environment):
    model = environment.configure(User)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_user_class")
async def async_user_class(environment):
    model = await environment.configure_async(AsyncUser)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="type_case_class")
def type_case_class(environment):
    model = environment.configure(TypeCase)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_type_case_class")
async def async_type_case_class(environment):
    model = await environment.configure_async(AsyncTypeCase)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="type_test_model")
def type_test_model(environment):
    model = environment.configure(TypeTestModel)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_type_test_model")
async def async_type_test_model(environment):
    model = await environment.configure_async(AsyncTypeTestModel)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="validated_user_class")
def validated_user_class(environment):
    model = environment.configure(ValidatedUser)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_validated_user_class")
async def async_validated_user_class(environment):
    model = await environment.configure_async(AsyncValidatedUser)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="validated_user")
def validated_user(environment):
    model = environment.configure(ValidatedProfile)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_validated_user")
async def async_validated_user(environment):
    model = await environment.configure_async(AsyncValidatedProfile)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="pydantic_validated_model")
def pydantic_validated_model(environment):
    model = environment.configure(PydanticValidatedModel)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_pydantic_validated_model")
async def async_pydantic_validated_model(environment):
    model = await environment.configure_async(AsyncPydanticValidatedModel)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="type_adapter_fixtures")
def type_adapter_fixtures(environment):
    model = environment.configure(TypeAdapterTest)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_type_adapter_fixtures")
async def async_type_adapter_fixtures(environment):
    model = await environment.configure_async(AsyncTypeAdapterTest)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="mapped_models_fixtures")
def mapped_models_fixtures(environment):
    models = tuple(
        environment.configure(model) for model in (MappedUser, MappedPost, MappedComment)
    )
    yield models
    _disconnect_models(models)


@pytest.fixture(name="async_mapped_models_fixtures")
async def async_mapped_models_fixtures(environment):
    models = tuple(
        [
            await environment.configure_async(model)
            for model in (AsyncMappedUser, AsyncMappedPost, AsyncMappedComment)
        ]
    )
    yield models
    await _disconnect_models_async(models)


@pytest.fixture(name="mixed_models_fixtures")
def mixed_models_fixtures(environment):
    models = tuple(
        environment.configure(model)
        for model in (ColumnMappingModel, MixedAnnotationModel)
    )
    yield models
    _disconnect_models(models)


@pytest.fixture(name="async_mixed_models_fixtures")
async def async_mixed_models_fixtures(environment):
    models = tuple(
        [
            await environment.configure_async(model)
            for model in (AsyncColumnMappingModel, AsyncMixedAnnotationModel)
        ]
    )
    yield models
    await _disconnect_models_async(models)


@pytest.fixture(name="bulk_user_class")
def bulk_user_class(environment):
    model = environment.configure(BulkUser)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_bulk_user_class")
async def async_bulk_user_class(environment):
    model = await environment.configure_async(AsyncBulkUser)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="order_item_class")
def order_item_class(environment):
    model = environment.configure(OrderItem)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_order_item_class")
async def async_order_item_class(environment):
    model = await environment.configure_async(AsyncOrderItem)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="order_class")
def order_class(environment):
    model = environment.configure(Order)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_order_class")
async def async_order_class(environment):
    model = await environment.configure_async(AsyncOrder)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="mapped_order_item_class")
def mapped_order_item_class(environment):
    model = environment.configure(MappedOrderItem)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_mapped_order_item_class")
async def async_mapped_order_item_class(environment):
    model = await environment.configure_async(AsyncMappedOrderItem)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_class")
def product_class(environment):
    model = environment.configure(Product)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_class")
async def async_product_class(environment):
    model = await environment.configure_async(AsyncProduct)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_form_a_class")
def product_form_a_class(environment):
    model = environment.configure(ProductFormA)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_form_a_class")
async def async_product_form_a_class(environment):
    model = await environment.configure_async(AsyncProductFormA)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_with_proxy_class")
def product_with_proxy_class(environment):
    model = environment.configure(ProductWithProxy)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_with_proxy_class")
async def async_product_with_proxy_class(environment):
    model = await environment.configure_async(AsyncProductWithProxy)
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_with_column_and_adapter_class")
def product_with_column_and_adapter_class(environment):
    model = environment.configure(ProductWithColumnAndAdapter)
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_with_column_and_adapter_class")
async def async_product_with_column_and_adapter_class(environment):
    model = await environment.configure_async(AsyncProductWithColumnAndAdapter)
    yield model
    await _disconnect_async(model)
