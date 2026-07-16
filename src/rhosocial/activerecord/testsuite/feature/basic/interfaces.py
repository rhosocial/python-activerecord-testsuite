# src/rhosocial/activerecord/testsuite/feature/basic/interfaces.py
"""
This file defines the interface (or contract) that a backend's test provider
must adhere to for the "basic" feature group.

By defining a standard interface, the generic tests in the testsuite can rely on
these methods being available, regardless of which database backend is actually
running the tests. Each backend must provide a concrete class that implements
these abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Type, List, Tuple
from rhosocial.activerecord.model import ActiveRecord


class BasicProviderBase(ABC):
    """
    The shared base for providers of the 'basic' feature tests, containing
    common non-I/O helper methods used by both sync and async providers.
    """

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """
        Should return a list of scenario names (e.g., ['memory', 'file'])
        that this backend supports for this test group.

        Returns:
            List[str]: A list of supported scenario names.
        """
        pass

    @abstractmethod
    def get_yes_no_adapter(self):
        """
        Returns an adapter instance for converting boolean True/False
        to 'yes'/'no' strings.
        """
        pass

    # --- Deprecated: subclasses should move these to the concrete interface ---


class IBasicSyncProvider(BasicProviderBase):
    """
    The sync interface for the provider of the 'basic' feature tests.
    """

    @abstractmethod
    def setup_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `User` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured User model class.
        """
        pass

    @abstractmethod
    def setup_type_case_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `TypeCase` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured TypeCase model class.
        """
        pass

    @abstractmethod
    def setup_type_test_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `TypeTestModel` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured TypeTestModel model class.
        """
        pass

    @abstractmethod
    def setup_validated_field_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `ValidatedFieldUser` model
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured ValidatedFieldUser model class.
        """
        pass

    @abstractmethod
    def setup_validated_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `ValidatedUser` model
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured ValidatedUser model class.
        """
        pass

    @abstractmethod
    def setup_pydantic_validated_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `PydanticValidatedModel`
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured PydanticValidatedModel class.
        """
        pass

    @abstractmethod
    def setup_mapped_models(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for `MappedUser`, `MappedPost`,
        and `MappedComment` models under a given scenario and return the
        configured model classes as a tuple.

        Returns:
            Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]: A tuple
            containing the configured MappedUser, MappedPost, and MappedComment model classes.
        """
        pass

    @abstractmethod
    def setup_mixed_models(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for models with mixed annotations
        (`ColumnMappingModel`, `MixedAnnotationModel`) under a given scenario
        and return the configured model classes as a tuple.

        Returns:
            Tuple[Type[ActiveRecord], ...]: A tuple containing the configured
            ColumnMappingModel and MixedAnnotationModel classes.
        """
        pass

    @abstractmethod
    def setup_type_adapter_model_and_schema(self) -> Type[ActiveRecord]:
        """
        Prepares the environment for type adapter tests.

        Implementers should:
        1. Define and execute the DDL for the 'type_adapter_tests' table.
        2. Define and configure the ActiveRecord model for this test.
        3. Return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured TypeAdapterTest model class.
        """
        pass

    @abstractmethod
    def setup_bulk_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `BulkUser` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured BulkUser model class.
        """
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass

    # --- Composite primary key model setup ---

    @abstractmethod
    def setup_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the order item model with
        composite primary key under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured OrderItem model class.
        """
        pass

    @abstractmethod
    def setup_order_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the order model under a given scenario
        and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured Order model class.
        """
        pass

    @abstractmethod
    def setup_mapped_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the mapped order item model with
        composite primary key (using UseColumn) and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured MappedOrderItem model class.
        """
        pass

    # --- Derived field model setup ---

    @abstractmethod
    def setup_product_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the product model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured Product model class.
        """
        pass

    @abstractmethod
    def setup_product_form_a_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the product model using Form A
        declaration (ClassVar assignment) and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured ProductFormA model class.
        """
        pass

    @abstractmethod
    def setup_product_with_proxy_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the product model using FieldProxy
        in derived field expressions and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured ProductWithProxy model class.
        """
        pass

    @abstractmethod
    def setup_product_with_column_and_adapter_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the product model using UseColumn
        and UseAdapter on derived fields and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured ProductWithColumnAndAdapter model class.
        """
        pass


class IBasicAsyncProvider(BasicProviderBase):
    """
    The async interface for the provider of the 'basic' feature tests.
    """

    @abstractmethod
    async def setup_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncUser` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncUser model class.
        """
        pass

    @abstractmethod
    async def setup_type_case_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncTypeCase` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncTypeCase model class.
        """
        pass

    @abstractmethod
    async def setup_type_test_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncTypeTestModel` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncTypeTestModel model class.
        """
        pass

    @abstractmethod
    async def setup_validated_field_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncValidatedFieldUser` model
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncValidatedFieldUser model class.
        """
        pass

    @abstractmethod
    async def setup_validated_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncValidatedUser` model
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncValidatedUser model class.
        """
        pass

    @abstractmethod
    async def setup_pydantic_validated_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncPydanticValidatedModel`
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncPydanticValidatedModel class.
        """
        pass

    @abstractmethod
    async def setup_mapped_models(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for `AsyncMappedUser`, `AsyncMappedPost`,
        and `AsyncMappedComment` models under a given scenario and return the
        configured model classes as a tuple.

        Returns:
            Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]: A tuple
            containing the configured AsyncMappedUser, AsyncMappedPost, and AsyncMappedComment model classes.
        """
        pass

    @abstractmethod
    async def setup_mixed_models(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for async models with mixed annotations
        (`AsyncColumnMappingModel`, `AsyncMixedAnnotationModel`) under a given scenario
        and return the configured model classes as a tuple.

        Returns:
            Tuple[Type[ActiveRecord], ...]: A tuple containing the configured
            AsyncColumnMappingModel and AsyncMixedAnnotationModel classes.
        """
        pass

    @abstractmethod
    async def setup_type_adapter_model_and_schema(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Prepares the environment for async type adapter tests.
        Implementers should:
        1. Define and execute the DDL for the 'type_adapter_tests' table.
        2. Define and configure the AsyncActiveRecord model for this test.
        3. Return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncTypeAdapterTest model class.
        """
        pass

    @abstractmethod
    async def setup_bulk_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `AsyncBulkUser` model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncBulkUser model class.
        """
        pass

    @abstractmethod
    async def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary async cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass

    # --- Composite primary key model setup (async) ---

    @abstractmethod
    async def setup_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async order item model with
        composite primary key under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncOrderItem model class.
        """
        pass

    @abstractmethod
    async def setup_order_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async order model under a given scenario
        and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncOrder model class.
        """
        pass

    @abstractmethod
    async def setup_mapped_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async mapped order item model with
        composite primary key (using UseColumn) and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncMappedOrderItem model class.
        """
        pass

    # --- Derived field model setup (async) ---

    @abstractmethod
    async def setup_product_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async product model under a
        given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncProduct model class.
        """
        pass

    @abstractmethod
    async def setup_product_form_a_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async product model using Form A
        declaration (ClassVar assignment) and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncProductFormA model class.
        """
        pass

    @abstractmethod
    async def setup_product_with_proxy_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async product model using FieldProxy
        in derived field expressions and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncProductWithProxy model class.
        """
        pass

    @abstractmethod
    async def setup_product_with_column_and_adapter_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async product model using UseColumn
        and UseAdapter on derived fields and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncProductWithColumnAndAdapter model class.
        """
        pass
