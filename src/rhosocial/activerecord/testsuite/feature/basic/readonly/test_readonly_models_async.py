# src/rhosocial/activerecord/testsuite/feature/basic/readonly/test_readonly_models_async.py
"""Read-only model contract (async).

``ReadOnlyMixin`` has no async variant because ``read_only()`` is a zero-I/O
predicate. This mirror proves the same single mixin gates every async write
path and that the declaration surface is identical.
"""

from typing import ClassVar, Optional

import pytest

from rhosocial.activerecord.backend.errors import DatabaseError, ReadOnlyError
from rhosocial.activerecord.base import ObjectDeclaration
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.interface import IReadOnlyBehavior
from rhosocial.activerecord.model import AsyncActiveRecord


class AsyncReadOnlyUser(AsyncActiveRecord, ReadOnlyMixin):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class AsyncWritableUser(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class AsyncOptedOutUser(AsyncActiveRecord, ReadOnlyMixin):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""
    @classmethod
    def read_only(cls):
        return False


class AsyncImplementsButWritable(AsyncActiveRecord, IReadOnlyBehavior):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class AsyncReadOnlyView(AsyncActiveRecord, ReadOnlyMixin):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""

    @classmethod
    def object_type(cls) -> ObjectDeclaration:
        return ObjectDeclaration.VIEW


@pytest.fixture
async def async_readonly_models(async_user_class):
    backend = async_user_class.backend()
    for model in (
        AsyncReadOnlyUser,
        AsyncWritableUser,
        AsyncOptedOutUser,
        AsyncImplementsButWritable,
        AsyncReadOnlyView,
    ):
        model.__backend__ = backend
    yield async_user_class


class TestAsyncReadonlyDeclaration:
    """The declaration, not a type test, decides."""

    def test_mixin_satisfies_the_interface(self):
        assert issubclass(ReadOnlyMixin, IReadOnlyBehavior)
        assert issubclass(AsyncReadOnlyUser, IReadOnlyBehavior)

    def test_read_only_reports_true(self):
        assert AsyncReadOnlyUser.read_only() is True

    def test_writable_model_has_no_read_only_at_all(self):
        assert not hasattr(AsyncWritableUser, "read_only")

    def test_writable_model_is_never_refused(self):
        AsyncWritableUser.refuse_read_only("save")

    def test_explicit_false_opts_back_out(self):
        assert AsyncOptedOutUser.read_only() is False
        AsyncOptedOutUser.refuse_read_only("save")

    def test_interface_implementor_reporting_false_still_writes(self):
        assert issubclass(AsyncImplementsButWritable, IReadOnlyBehavior)
        assert AsyncImplementsButWritable.read_only() is False
        AsyncImplementsButWritable.refuse_read_only("save")

    def test_read_only_is_orthogonal_to_the_primary_key(self):
        assert AsyncReadOnlyUser.primary_key_columns() == ("id",)
        assert AsyncWritableUser.primary_key_columns() == ("id",)

    def test_read_only_model_can_declare_a_view_object_type(self):
        assert AsyncReadOnlyUser.object_type() is ObjectDeclaration.TABLE
        assert AsyncReadOnlyView.object_type() is ObjectDeclaration.VIEW


class TestAsyncReadonlyWriteRefusal:
    async def test_save_raises(self, async_readonly_models):
        with pytest.raises(ReadOnlyError, match="save is not allowed on read-only model"):
            await AsyncReadOnlyUser(username="x").save()

    async def test_delete_raises(self, async_readonly_models):
        record = AsyncReadOnlyUser(id=1, username="x")
        record._is_from_db = True
        with pytest.raises(ReadOnlyError, match="delete is not allowed"):
            await record.delete()

    def test_error_names_model_and_operation(self):
        with pytest.raises(ReadOnlyError) as excinfo:
            AsyncReadOnlyUser.refuse_read_only("bulk_delete")
        assert excinfo.value.model_name == "AsyncReadOnlyUser"
        assert excinfo.value.operation == "bulk_delete"

    def test_error_is_a_database_error(self):
        assert issubclass(ReadOnlyError, DatabaseError)


class TestAsyncReadonlyClassLevelRefusal:
    async def test_bulk_create_raises(self, async_readonly_models):
        with pytest.raises(ReadOnlyError, match="bulk_create"):
            await AsyncReadOnlyUser.bulk_create([AsyncReadOnlyUser(username="x")])

    async def test_bulk_update_raises(self, async_readonly_models):
        with pytest.raises(ReadOnlyError, match="bulk_update"):
            await AsyncReadOnlyUser.bulk_update([AsyncReadOnlyUser(id=1, username="x")], ["username"])

    async def test_bulk_delete_raises(self, async_readonly_models):
        with pytest.raises(ReadOnlyError, match="bulk_delete"):
            await AsyncReadOnlyUser.bulk_delete([AsyncReadOnlyUser(id=1, username="x")])

    async def test_update_all_raises(self, async_readonly_models):
        query = AsyncReadOnlyUser.query().where(AsyncReadOnlyUser.c.id == 1)
        with pytest.raises(ReadOnlyError, match="update_all"):
            await query.update_all({"username": "y"})

    async def test_delete_all_raises(self, async_readonly_models):
        query = AsyncReadOnlyUser.query().where(AsyncReadOnlyUser.c.id == 1)
        with pytest.raises(ReadOnlyError, match="delete_all"):
            await query.delete_all()


class TestAsyncReadonlyReadsStillWork:
    async def test_query_works(self, async_readonly_models):
        assert isinstance(await AsyncReadOnlyUser.query().all(), list)

    async def test_count_works(self, async_readonly_models):
        assert await AsyncReadOnlyUser.query().count() >= 0

    async def test_where_works(self, async_readonly_models):
        assert isinstance(await AsyncReadOnlyUser.query().where(AsyncReadOnlyUser.c.id == 1).all(), list)


class TestAsyncReadonlyFindOneOrCreate:
    """``find_one_or_create`` keeps the read path but refuses creation."""

    _EXISTING_USERNAME = "__readonly_find_one_or_create_existing__"
    _EXISTING_EMAIL = "readonly-find-one-or-create@example.com"
    _MISSING_USERNAME = "__readonly_find_one_or_create_missing__"

    async def test_existing_row_is_returned_without_writing(
        self, async_readonly_models
    ):
        seed = async_readonly_models(
            username=self._EXISTING_USERNAME,
            email=self._EXISTING_EMAIL,
            age=25,
        )
        await seed.save()
        record, created = await AsyncReadOnlyUser.find_one_or_create(
            username=self._EXISTING_USERNAME
        )
        assert created is False
        assert record is not None
        assert record.id == seed.id

    async def test_missing_row_refuses_creation(self, async_readonly_models):
        with pytest.raises(
            ReadOnlyError, match="save is not allowed on read-only model"
        ):
            await AsyncReadOnlyUser.find_one_or_create(
                username=self._MISSING_USERNAME
            )
