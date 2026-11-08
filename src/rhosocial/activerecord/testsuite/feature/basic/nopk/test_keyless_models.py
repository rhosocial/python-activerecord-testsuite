# src/rhosocial/activerecord/testsuite/feature/basic/nopk/test_keyless_models.py
"""Keyless model contract (sync).

``__primary_key__ = None`` is a declared shape: the relation has no single-row
identity. Queries, ordering, grouping, aggregation and counting keep working;
only identity-based access is unavailable, and it is refused with
``UnaddressableRecordError`` instead of leaking a ``TypeError`` from
``getattr``.

This contract reuses the provider's existing ``users`` table, so it adds no
DDL and stays backend-neutral. Keyless-ness is orthogonal to read-only-ness in
both directions.
"""

from typing import ClassVar, Optional

import pytest

from rhosocial.activerecord.backend.errors import DatabaseError, UnaddressableRecordError
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.model import ActiveRecord


class KeylessUser(ActiveRecord):
    """Mapped onto a keyless projection of the users table."""
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    __primary_key__ = None
    id: Optional[int] = None
    username: str = ""


class KeylessReadOnlyUser(ActiveRecord, ReadOnlyMixin):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    __primary_key__ = None
    id: Optional[int] = None
    username: str = ""


class ReadOnlyWithKeyUser(ActiveRecord, ReadOnlyMixin):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


class NormalUser(ActiveRecord):
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    username: str = ""


@pytest.fixture
def keyless_models(user_class):
    backend = user_class.backend()
    for model in (KeylessUser, KeylessReadOnlyUser, ReadOnlyWithKeyUser, NormalUser):
        model.__backend__ = backend
    yield user_class


class TestKeylessDeclaration:
    def test_none_is_an_accepted_declaration(self):
        assert KeylessUser.primary_key() is None

    def test_addressable_reports_false(self):
        assert KeylessUser.addressable() is False

    def test_addressable_reports_true_for_a_normal_model(self):
        assert NormalUser.addressable() is True

    def test_key_columns_are_empty_not_none(self):
        assert KeylessUser.primary_key_columns() == ()
        assert KeylessUser.primary_key_fields() == ()

    def test_key_columns_never_contain_none(self):
        for model in (KeylessUser, KeylessReadOnlyUser, ReadOnlyWithKeyUser, NormalUser):
            assert None not in model.primary_key_columns(), model.__name__
            assert None not in model.primary_key_fields(), model.__name__

    def test_is_composite_pk_is_false(self):
        assert KeylessUser.is_composite_pk() is False

    def test_normal_model_is_unchanged(self):
        assert NormalUser.primary_key_columns() == ("id",)
        assert NormalUser.primary_key_fields() == ("id",)


class TestKeylessIsNewRecord:
    def test_a_constructed_record_is_new(self):
        assert KeylessUser(username="x").is_new_record is True

    def test_a_row_loaded_from_the_database_is_not_new(self):
        loaded = KeylessUser(username="x")
        loaded._is_from_db = True
        assert loaded.is_new_record is False

    def test_keyless_model_has_no_identity_to_inspect(self):
        assert KeylessUser.primary_key_fields() == ()


class TestKeylessQueriesKeepWorking:
    def test_query_works(self, keyless_models):
        assert isinstance(KeylessUser.query().all(), list)

    def test_count_works(self, keyless_models):
        assert KeylessUser.query().count() >= 0

    def test_where_works(self, keyless_models):
        assert isinstance(KeylessUser.query().where(KeylessUser.c.id == 1).all(), list)

    def test_order_by_works(self, keyless_models):
        assert isinstance(KeylessUser.query().order_by(KeylessUser.c.id).all(), list)


class TestKeylessIdentityAccessIsRefused:
    def test_find_one_by_value(self, keyless_models):
        with pytest.raises(UnaddressableRecordError, match="find_one"):
            KeylessUser.find_one(1)

    def test_find_all_by_value_list(self, keyless_models):
        with pytest.raises(UnaddressableRecordError, match="find_all"):
            KeylessUser.find_all([1, 2])

    def test_refresh(self):
        with pytest.raises(UnaddressableRecordError, match="refresh"):
            KeylessUser(username="x").refresh()

    def test_the_error_names_model_and_operation(self, keyless_models):
        with pytest.raises(UnaddressableRecordError) as excinfo:
            KeylessUser.find_one(1)
        assert excinfo.value.model_name == "KeylessUser"
        assert excinfo.value.operation == "find_one"

    def test_the_error_is_a_database_error(self):
        assert issubclass(UnaddressableRecordError, DatabaseError)

    def test_the_error_suggests_the_alternative(self, keyless_models):
        with pytest.raises(UnaddressableRecordError) as excinfo:
            KeylessUser.find_one(1)
        assert "where(...)" in str(excinfo.value)


class TestKeylessBulkIdentityIsRefused:
    def test_bulk_update_refused(self, keyless_models):
        with pytest.raises(UnaddressableRecordError, match="bulk_update"):
            KeylessUser.bulk_update([KeylessUser(username="x")], ["username"])

    def test_bulk_delete_refused(self, keyless_models):
        with pytest.raises(UnaddressableRecordError, match="bulk_delete"):
            KeylessUser.bulk_delete([KeylessUser(username="x")])


class TestKeylessNonIdentityConditionsStillWork:
    def test_find_all_with_no_condition(self, keyless_models):
        assert isinstance(KeylessUser.find_all(), list)

    def test_find_one_with_a_predicate(self, keyless_models):
        # A predicate is not a primary-key condition, so it is not refused;
        # the query simply runs. The users table may be empty, which is why
        # only the absence of the refusal is asserted.
        result = KeylessUser.find_one(KeylessUser.c.id == 1)
        assert result is None or result.id == 1


class TestKeylessOrthogonality:
    def test_keyless_and_read_only_together(self, keyless_models):
        assert KeylessReadOnlyUser.addressable() is False
        assert KeylessReadOnlyUser.read_only() is True

    def test_keyless_read_only_refuses_writes(self, keyless_models):
        from rhosocial.activerecord.backend.errors import ReadOnlyError

        with pytest.raises(ReadOnlyError):
            KeylessReadOnlyUser(username="x").save()

    def test_read_only_but_addressable(self, keyless_models):
        assert ReadOnlyWithKeyUser.addressable() is True
        assert ReadOnlyWithKeyUser.read_only() is True

    def test_read_only_with_a_key_still_refuses_by_identity(self, keyless_models):
        from rhosocial.activerecord.backend.errors import ReadOnlyError

        with pytest.raises(ReadOnlyError):
            ReadOnlyWithKeyUser(username="x").save()
