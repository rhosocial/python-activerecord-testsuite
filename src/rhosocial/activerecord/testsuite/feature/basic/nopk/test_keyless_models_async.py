# src/rhosocial/activerecord/testsuite/feature/basic/nopk/test_keyless_models_async.py
"""Keyless model contract (async).

``__primary_key__ = None`` is a declaration, not an async concern. The same
decision points answer for the async family: reads keep working, identity-based
access is refused, and keyless-ness stays orthogonal to read-only-ness.
"""

from typing import ClassVar, Optional

import pytest

from rhosocial.activerecord.backend.errors import (
    DatabaseError,
    ReadOnlyError,
    UnaddressableRecordError,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.model import AsyncActiveRecord


class AsyncKeylessUser(AsyncActiveRecord):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    __primary_key__ = None
    id: Optional[int] = None
    username: str = ""


class AsyncKeylessReadOnlyUser(AsyncActiveRecord, ReadOnlyMixin):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    __primary_key__ = None
    id: Optional[int] = None
    username: str = ""


class AsyncReadOnlyWithKeyUser(AsyncActiveRecord, ReadOnlyMixin):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class AsyncNormalUser(AsyncActiveRecord):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


@pytest.fixture
async def async_keyless_models(async_user_class):
    backend = async_user_class.backend()
    for model in (
        AsyncKeylessUser,
        AsyncKeylessReadOnlyUser,
        AsyncReadOnlyWithKeyUser,
        AsyncNormalUser,
    ):
        model.__backend__ = backend
    yield async_user_class


class TestAsyncKeylessDeclaration:
    def test_none_is_an_accepted_declaration(self):
        assert AsyncKeylessUser.primary_key() is None

    def test_addressable_reports_false(self):
        assert AsyncKeylessUser.addressable() is False

    def test_addressable_reports_true_for_a_normal_model(self):
        assert AsyncNormalUser.addressable() is True

    def test_key_columns_are_empty_not_none(self):
        assert AsyncKeylessUser.primary_key_columns() == ()
        assert AsyncKeylessUser.primary_key_fields() == ()

    def test_key_columns_never_contain_none(self):
        for model in (
            AsyncKeylessUser,
            AsyncKeylessReadOnlyUser,
            AsyncReadOnlyWithKeyUser,
            AsyncNormalUser,
        ):
            assert None not in model.primary_key_columns(), model.__name__
            assert None not in model.primary_key_fields(), model.__name__

    def test_is_composite_pk_is_false(self):
        assert AsyncKeylessUser.is_composite_pk() is False

    def test_normal_model_is_unchanged(self):
        assert AsyncNormalUser.primary_key_columns() == ("id",)
        assert AsyncNormalUser.primary_key_fields() == ("id",)


class TestAsyncKeylessIsNewRecord:
    def test_a_constructed_record_is_new(self):
        assert AsyncKeylessUser(username="x").is_new_record is True

    def test_a_row_loaded_from_the_database_is_not_new(self):
        loaded = AsyncKeylessUser(username="x")
        loaded._is_from_db = True
        assert loaded.is_new_record is False

    def test_keyless_model_has_no_identity_to_inspect(self):
        assert AsyncKeylessUser.primary_key_fields() == ()


class TestAsyncKeylessQueriesKeepWorking:
    async def test_query_works(self, async_keyless_models):
        assert isinstance(await AsyncKeylessUser.query().all(), list)

    async def test_count_works(self, async_keyless_models):
        assert await AsyncKeylessUser.query().count() >= 0

    async def test_where_works(self, async_keyless_models):
        assert isinstance(await AsyncKeylessUser.query().where(AsyncKeylessUser.c.id == 1).all(), list)

    async def test_order_by_works(self, async_keyless_models):
        assert isinstance(await AsyncKeylessUser.query().order_by(AsyncKeylessUser.c.id).all(), list)


class TestAsyncKeylessIdentityAccessIsRefused:
    async def test_find_one_by_value(self, async_keyless_models):
        with pytest.raises(UnaddressableRecordError, match="find_one"):
            await AsyncKeylessUser.find_one(1)

    async def test_find_all_by_value_list(self, async_keyless_models):
        with pytest.raises(UnaddressableRecordError, match="find_all"):
            await AsyncKeylessUser.find_all([1, 2])

    async def test_refresh(self):
        with pytest.raises(UnaddressableRecordError, match="refresh"):
            await AsyncKeylessUser(username="x").refresh()

    async def test_the_error_names_model_and_operation(self, async_keyless_models):
        with pytest.raises(UnaddressableRecordError) as excinfo:
            await AsyncKeylessUser.find_one(1)
        assert excinfo.value.model_name == "AsyncKeylessUser"
        assert excinfo.value.operation == "find_one"

    def test_the_error_is_a_database_error(self):
        assert issubclass(UnaddressableRecordError, DatabaseError)

    async def test_the_error_suggests_the_alternative(self, async_keyless_models):
        with pytest.raises(UnaddressableRecordError) as excinfo:
            await AsyncKeylessUser.find_one(1)
        assert "where(...)" in str(excinfo.value)


class TestAsyncKeylessBulkIdentityIsRefused:
    async def test_bulk_update_refused(self, async_keyless_models):
        with pytest.raises(UnaddressableRecordError, match="bulk_update"):
            await AsyncKeylessUser.bulk_update([AsyncKeylessUser(username="x")], ["username"])

    async def test_bulk_delete_refused(self, async_keyless_models):
        with pytest.raises(UnaddressableRecordError, match="bulk_delete"):
            await AsyncKeylessUser.bulk_delete([AsyncKeylessUser(username="x")])


class TestAsyncKeylessNonIdentityConditionsStillWork:
    async def test_find_all_with_no_condition(self, async_keyless_models):
        assert isinstance(await AsyncKeylessUser.find_all(), list)

    async def test_find_one_with_a_predicate(self, async_keyless_models):
        result = await AsyncKeylessUser.find_one(AsyncKeylessUser.c.id == 1)
        assert result is None or result.id == 1


class TestAsyncKeylessOrthogonality:
    async def test_keyless_and_read_only_together(self, async_keyless_models):
        assert AsyncKeylessReadOnlyUser.addressable() is False
        assert AsyncKeylessReadOnlyUser.read_only() is True

    async def test_keyless_read_only_refuses_writes(self, async_keyless_models):
        with pytest.raises(ReadOnlyError):
            await AsyncKeylessReadOnlyUser(username="x").save()

    async def test_read_only_but_addressable(self, async_keyless_models):
        assert AsyncReadOnlyWithKeyUser.addressable() is True
        assert AsyncReadOnlyWithKeyUser.read_only() is True

    async def test_read_only_with_a_key_still_refuses_by_identity(self, async_keyless_models):
        with pytest.raises(ReadOnlyError):
            await AsyncReadOnlyWithKeyUser(username="x").save()
