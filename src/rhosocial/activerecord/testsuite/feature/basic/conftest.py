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
def user_class(database_config):
    scenario, config, _name = database_config
    User.configure(config, scenario.backend_class)
    model = User
    yield model
    _disconnect(model)


@pytest.fixture(name="async_user_class")
async def async_user_class(database_config):
    scenario, config, _name = database_config
    await AsyncUser.configure(config, scenario.async_backend_class)
    model = AsyncUser
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="validated_user_class")
def validated_user_class(database_config):
    scenario, config, _name = database_config
    ValidatedUser.configure(config, scenario.backend_class)
    model = ValidatedUser
    yield model
    _disconnect(model)


@pytest.fixture(name="async_validated_user_class")
async def async_validated_user_class(database_config):
    scenario, config, _name = database_config
    await AsyncValidatedUser.configure(config, scenario.async_backend_class)
    model = AsyncValidatedUser
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="validated_user")
def validated_user(database_config):
    scenario, config, _name = database_config
    ValidatedProfile.configure(config, scenario.backend_class)
    model = ValidatedProfile
    yield model
    _disconnect(model)


@pytest.fixture(name="async_validated_user")
async def async_validated_user(database_config):
    scenario, config, _name = database_config
    await AsyncValidatedProfile.configure(config, scenario.async_backend_class)
    model = AsyncValidatedProfile
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="pydantic_validated_model")
def pydantic_validated_model(database_config):
    scenario, config, _name = database_config
    PydanticValidatedModel.configure(config, scenario.backend_class)
    model = PydanticValidatedModel
    yield model
    _disconnect(model)


@pytest.fixture(name="async_pydantic_validated_model")
async def async_pydantic_validated_model(database_config):
    scenario, config, _name = database_config
    await AsyncPydanticValidatedModel.configure(config, scenario.async_backend_class)
    model = AsyncPydanticValidatedModel
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="type_adapter_fixtures")
def type_adapter_fixtures(database_config):
    scenario, config, _name = database_config
    TypeAdapterTest.configure(config, scenario.backend_class)
    model = TypeAdapterTest
    yield model
    _disconnect(model)


@pytest.fixture(name="async_type_adapter_fixtures")
async def async_type_adapter_fixtures(database_config):
    scenario, config, _name = database_config
    await AsyncTypeAdapterTest.configure(config, scenario.async_backend_class)
    model = AsyncTypeAdapterTest
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="mapped_models_fixtures")
def mapped_models_fixtures(database_config):
    scenario, config, _name = database_config
    models = (MappedUser, MappedPost, MappedComment)
    for model in models:
        model.configure(config, scenario.backend_class)
    yield models
    _disconnect_models(models)


@pytest.fixture(name="async_mapped_models_fixtures")
async def async_mapped_models_fixtures(database_config):
    scenario, config, _name = database_config
    models = (AsyncMappedUser, AsyncMappedPost, AsyncMappedComment)
    for model in models:
        await model.configure(config, scenario.async_backend_class)
    yield models
    await _disconnect_models_async(models)


@pytest.fixture(name="mixed_models_fixtures")
def mixed_models_fixtures(database_config):
    scenario, config, _name = database_config
    models = (ColumnMappingModel, MixedAnnotationModel)
    for model in models:
        model.configure(config, scenario.backend_class)
    yield models
    _disconnect_models(models)


@pytest.fixture(name="async_mixed_models_fixtures")
async def async_mixed_models_fixtures(database_config):
    scenario, config, _name = database_config
    models = (AsyncColumnMappingModel, AsyncMixedAnnotationModel)
    for model in models:
        await model.configure(config, scenario.async_backend_class)
    yield models
    await _disconnect_models_async(models)


@pytest.fixture(name="bulk_user_class")
def bulk_user_class(database_config):
    scenario, config, _name = database_config
    BulkUser.configure(config, scenario.backend_class)
    model = BulkUser
    yield model
    _disconnect(model)


@pytest.fixture(name="async_bulk_user_class")
async def async_bulk_user_class(database_config):
    scenario, config, _name = database_config
    await AsyncBulkUser.configure(config, scenario.async_backend_class)
    model = AsyncBulkUser
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_class")
def product_class(database_config):
    scenario, config, _name = database_config
    Product.configure(config, scenario.backend_class)
    model = Product
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_class")
async def async_product_class(database_config):
    scenario, config, _name = database_config
    await AsyncProduct.configure(config, scenario.async_backend_class)
    model = AsyncProduct
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_form_a_class")
def product_form_a_class(database_config):
    scenario, config, _name = database_config
    ProductFormA.configure(config, scenario.backend_class)
    model = ProductFormA
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_form_a_class")
async def async_product_form_a_class(database_config):
    scenario, config, _name = database_config
    await AsyncProductFormA.configure(config, scenario.async_backend_class)
    model = AsyncProductFormA
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_with_proxy_class")
def product_with_proxy_class(database_config):
    scenario, config, _name = database_config
    ProductWithProxy.configure(config, scenario.backend_class)
    model = ProductWithProxy
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_with_proxy_class")
async def async_product_with_proxy_class(database_config):
    scenario, config, _name = database_config
    await AsyncProductWithProxy.configure(config, scenario.async_backend_class)
    model = AsyncProductWithProxy
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="product_with_column_and_adapter_class")
def product_with_column_and_adapter_class(database_config):
    scenario, config, _name = database_config
    ProductWithColumnAndAdapter.configure(config, scenario.backend_class)
    model = ProductWithColumnAndAdapter
    yield model
    _disconnect(model)


@pytest.fixture(name="async_product_with_column_and_adapter_class")
async def async_product_with_column_and_adapter_class(database_config):
    scenario, config, _name = database_config
    await AsyncProductWithColumnAndAdapter.configure(config, scenario.async_backend_class)
    model = AsyncProductWithColumnAndAdapter
    yield model
    await _disconnect_async(model)
