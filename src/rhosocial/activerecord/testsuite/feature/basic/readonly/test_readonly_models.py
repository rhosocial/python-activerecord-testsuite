# src/rhosocial/activerecord/testsuite/feature/basic/readonly/test_readonly_models.py
"""Read-only model contract (sync).

``ReadOnlyMixin`` is opt-in and orthogonal: read-only-ness is a static
declaration independent of the primary key and of the physical object the model
maps. A read-only table may have an auto-generated key, and a keyless table may
be writable.

This contract deliberately reuses the provider's existing ``users`` table and
creates nothing. That keeps it backend-neutral: the assertions are about
metadata, the gate ordering, and the error type, all of which are decided
before SQL is issued. The "no SQL reached the database" assertion is
SQLite-specific and lives in the core suite, not here.
"""

from typing import ClassVar, Optional

import pytest

from rhosocial.activerecord.backend.errors import DatabaseError, ReadOnlyError
from rhosocial.activerecord.base import ObjectDeclaration
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.interface import IReadOnlyBehavior
from rhosocial.activerecord.model import ActiveRecord


class ReadOnlyUser(ActiveRecord, ReadOnlyMixin):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class WritableUser(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class OptedOutUser(ActiveRecord, ReadOnlyMixin):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""
    @classmethod
    def read_only(cls):
        return False


class ImplementsButWritable(ActiveRecord, IReadOnlyBehavior):
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class ReadOnlyView(ActiveRecord, ReadOnlyMixin):
    """A read-only model that declares it maps a view."""

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
def readonly_models(user_class):
    backend = user_class.backend()
    for model in (
        ReadOnlyUser,
        WritableUser,
        OptedOutUser,
        ImplementsButWritable,
        ReadOnlyView,
    ):
        model.__backend__ = backend
    yield user_class


class TestReadonlyDeclaration:
    """The declaration, not a type test, decides."""

    def test_mixin_satisfies_the_interface(self):
        assert issubclass(ReadOnlyMixin, IReadOnlyBehavior)
        assert issubclass(ReadOnlyUser, IReadOnlyBehavior)

    def test_read_only_reports_true(self):
        assert ReadOnlyUser.read_only() is True

    def test_writable_model_has_no_read_only_at_all(self):
        assert not hasattr(WritableUser, "read_only")

    def test_writable_model_is_never_refused(self):
        WritableUser.refuse_read_only("save")

    def test_explicit_false_opts_back_out(self):
        assert OptedOutUser.read_only() is False
        OptedOutUser.refuse_read_only("save")

    def test_interface_implementor_reporting_false_still_writes(self):
        assert issubclass(ImplementsButWritable, IReadOnlyBehavior)
        assert ImplementsButWritable.read_only() is False
        ImplementsButWritable.refuse_read_only("save")

    def test_read_only_is_orthogonal_to_the_primary_key(self):
        assert ReadOnlyUser.primary_key_columns() == ("id",)
        assert WritableUser.primary_key_columns() == ("id",)

    def test_read_only_model_can_declare_a_view_object_type(self):
        assert ReadOnlyUser.object_type() is ObjectDeclaration.TABLE
        assert ReadOnlyView.object_type() is ObjectDeclaration.VIEW


class TestReadonlyWriteRefusal:
    def test_save_raises(self, readonly_models):
        with pytest.raises(ReadOnlyError, match="save is not allowed on read-only model"):
            ReadOnlyUser(username="x").save()

    def test_delete_raises(self, readonly_models):
        record = ReadOnlyUser(id=1, username="x")
        record._is_from_db = True
        with pytest.raises(ReadOnlyError, match="delete is not allowed"):
            record.delete()

    def test_error_names_model_and_operation(self):
        with pytest.raises(ReadOnlyError) as excinfo:
            ReadOnlyUser.refuse_read_only("bulk_delete")
        assert excinfo.value.model_name == "ReadOnlyUser"
        assert excinfo.value.operation == "bulk_delete"

    def test_error_is_a_database_error(self):
        assert issubclass(ReadOnlyError, DatabaseError)


class TestReadonlyClassLevelRefusal:
    def test_bulk_create_raises(self, readonly_models):
        with pytest.raises(ReadOnlyError, match="bulk_create"):
            ReadOnlyUser.bulk_create([ReadOnlyUser(username="x")])

    def test_bulk_update_raises(self, readonly_models):
        with pytest.raises(ReadOnlyError, match="bulk_update"):
            ReadOnlyUser.bulk_update([ReadOnlyUser(id=1, username="x")], ["username"])

    def test_bulk_delete_raises(self, readonly_models):
        with pytest.raises(ReadOnlyError, match="bulk_delete"):
            ReadOnlyUser.bulk_delete([ReadOnlyUser(id=1, username="x")])

    def test_update_all_raises(self, readonly_models):
        with pytest.raises(ReadOnlyError, match="update_all"):
            ReadOnlyUser.query().where(ReadOnlyUser.c.id == 1).update_all({"username": "y"})

    def test_delete_all_raises(self, readonly_models):
        with pytest.raises(ReadOnlyError, match="delete_all"):
            ReadOnlyUser.query().where(ReadOnlyUser.c.id == 1).delete_all()


class TestReadonlyReadsStillWork:
    def test_query_works(self, readonly_models):
        assert isinstance(ReadOnlyUser.query().all(), list)

    def test_count_works(self, readonly_models):
        assert ReadOnlyUser.query().count() >= 0

    def test_where_works(self, readonly_models):
        assert isinstance(ReadOnlyUser.query().where(ReadOnlyUser.c.id == 1).all(), list)


class TestReadonlyFindOneOrCreate:
    """``find_one_or_create`` keeps the read path but refuses creation."""

    _EXISTING_USERNAME = "__readonly_find_one_or_create_existing__"
    _EXISTING_EMAIL = "readonly-find-one-or-create@example.com"
    _MISSING_USERNAME = "__readonly_find_one_or_create_missing__"

    def test_existing_row_is_returned_without_writing(self, readonly_models):
        seed = readonly_models(
            username=self._EXISTING_USERNAME,
            email=self._EXISTING_EMAIL,
            age=25,
        )
        seed.save()
        record, created = ReadOnlyUser.find_one_or_create(
            username=self._EXISTING_USERNAME
        )
        assert created is False
        assert record is not None
        assert record.id == seed.id

    def test_missing_row_refuses_creation(self, readonly_models):
        with pytest.raises(
            ReadOnlyError, match="save is not allowed on read-only model"
        ):
            ReadOnlyUser.find_one_or_create(username=self._MISSING_USERNAME)
