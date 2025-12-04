# src/rhosocial/activerecord/testsuite/feature/basic/test_type_adapter.py
from datetime import datetime, timezone


class TestTypeAdapter:

    def test_optional_string_conversion(self, type_adapter_fixtures):
        """Tests that Optional[str] is handled correctly."""
        TypeAdapterTest = type_adapter_fixtures
        # Test with a value
        rec1 = TypeAdapterTest(name="test_with_str", optional_name="optional_value", custom_bool=False)
        rec1.save()
        found_rec1 = TypeAdapterTest.find_one(rec1.id)
        assert isinstance(found_rec1.optional_name, str)
        assert found_rec1.optional_name == "optional_value"

        # Test with None
        rec2 = TypeAdapterTest(name="test_with_none", optional_name=None, custom_bool=False)
        rec2.save()
        found_rec2 = TypeAdapterTest.find_one(rec2.id)
        assert found_rec2.optional_name is None

    def test_optional_int_conversion(self, type_adapter_fixtures):
        """Tests that Optional[int] is handled correctly."""
        TypeAdapterTest = type_adapter_fixtures
        # Test with a value
        rec1 = TypeAdapterTest(name="test_with_int", optional_age=30, custom_bool=False)
        rec1.save()
        found_rec1 = TypeAdapterTest.find_one(rec1.id)
        assert isinstance(found_rec1.optional_age, int)
        assert found_rec1.optional_age == 30

        # Test with None
        rec2 = TypeAdapterTest(name="test_with_none_age", optional_age=None, custom_bool=False)
        rec2.save()
        found_rec2 = TypeAdapterTest.find_one(rec2.id)
        assert found_rec2.optional_age is None

    def test_optional_datetime_conversion(self, type_adapter_fixtures):
        """Tests that Optional[datetime] is handled correctly by its adapter."""
        TypeAdapterTest = type_adapter_fixtures
        now = datetime.now(timezone.utc).replace(microsecond=0)
        # Test with a value
        rec1 = TypeAdapterTest(name="test_with_datetime", last_login=now, custom_bool=False)
        rec1.save()
        found_rec1 = TypeAdapterTest.find_one(rec1.id)
        assert isinstance(found_rec1.last_login, datetime)
        assert found_rec1.last_login == now

        # Test with None
        rec2 = TypeAdapterTest(name="test_with_none_datetime", last_login=None, custom_bool=False)
        rec2.save()
        found_rec2 = TypeAdapterTest.find_one(rec2.id)
        assert found_rec2.last_login is None

    def test_optional_bool_conversion(self, type_adapter_fixtures):
        """Tests that Optional[bool] is handled correctly by its adapter."""
        TypeAdapterTest = type_adapter_fixtures
        # Test with a value
        rec1 = TypeAdapterTest(name="test_with_bool_true", is_premium=True, custom_bool=False)
        rec1.save()
        found_rec1 = TypeAdapterTest.find_one(rec1.id)
        assert found_rec1.is_premium is True

        rec2 = TypeAdapterTest(name="test_with_bool_false", is_premium=False, custom_bool=False)
        rec2.save()
        found_rec2 = TypeAdapterTest.find_one(rec2.id)
        assert found_rec2.is_premium is False

        # Test with None
        rec3 = TypeAdapterTest(name="test_with_none_bool", is_premium=None, custom_bool=False)
        rec3.save()
        found_rec3 = TypeAdapterTest.find_one(rec3.id)
        assert found_rec3.is_premium is None

    def test_non_optional_field_no_regression(self, type_adapter_fixtures):
        """Tests that a simple non-optional field is not affected."""
        TypeAdapterTest = type_adapter_fixtures
        rec = TypeAdapterTest(name="simple_string", custom_bool=False)
        rec.save()
        found_rec = TypeAdapterTest.find_one(rec.id)
        assert isinstance(found_rec.name, str)
        assert found_rec.name == "simple_string"

    def test_unsupported_union_is_handled_gracefully(self, type_adapter_fixtures):
        """
        Tests that a Union of multiple non-None types is handled gracefully.
        """
        TypeAdapterTest = type_adapter_fixtures
        # Save a string value to a field that expects Union[str, int].
        # The `to_database` part will work fine as it will use the string adapter.
        placeholder = TypeAdapterTest.backend().dialect.get_placeholder()
        TypeAdapterTest.backend().execute(
            f"INSERT INTO type_adapter_tests (id, name, unsupported_union, custom_bool) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
            (1, "test_unsupported_union", "some_string", "no")
        )

        # When converting from the database, the type adapter logic for Optional[T]
        # will be skipped for Union[str, int]. Pydantic is then able to correctly
        # coerce the string value from the DB into the Union type.
        # Therefore, no error should be raised.
        found_rec = TypeAdapterTest.find_one(1)

        assert found_rec is not None
        assert found_rec.unsupported_union == "some_string"
        assert isinstance(found_rec.unsupported_union, str)

    def test_db_null_with_non_optional_field_raises_error(self, type_adapter_fixtures):
        """
        Tests that inserting a NULL into a NOT NULL column raises an IntegrityError.
        """
        TypeAdapterTest = type_adapter_fixtures
        from rhosocial.activerecord.backend.errors import IntegrityError
        import pytest

        # Manually trying to insert a record with NULL for the non-optional 'name' field
        # should violate the table's NOT NULL constraint.
        placeholder = TypeAdapterTest.backend().dialect.get_placeholder()
        with pytest.raises(IntegrityError) as exc_info:
            TypeAdapterTest.backend().execute(f"INSERT INTO type_adapter_tests (id, name) VALUES ({placeholder}, {placeholder})", (1, None))

        error_message = str(exc_info.value)
        # Check for SQLite's message OR MySQL's message
        assert ("NOT NULL constraint failed" in error_message or "cannot be null" in error_message or "violates not-null constraint" in error_message)

    def test_annotated_custom_adapter(self, type_adapter_fixtures):
        """Tests that a field-specific adapter assigned via Annotation works correctly."""
        TypeAdapterTest = type_adapter_fixtures
        # Test True value
        rec_true = TypeAdapterTest(name="custom_true", custom_bool=True)
        rec_true.save()
        placeholder = TypeAdapterTest.backend().dialect.get_placeholder()
        # Verify raw data in DB is 'yes'
        raw_true = TypeAdapterTest.backend().fetch_one(f"SELECT custom_bool FROM type_adapter_tests WHERE id = {placeholder}", (rec_true.id,))
        assert raw_true["custom_bool"] == "yes"

        # Verify that reading it back converts it to True
        found_true = TypeAdapterTest.find_one(rec_true.id)
        assert found_true.custom_bool is True

        # Test False value
        rec_false = TypeAdapterTest(name="custom_false", custom_bool=False)
        rec_false.save()

        # Verify raw data in DB is 'no'
        raw_false = TypeAdapterTest.backend().fetch_one(f"SELECT custom_bool FROM type_adapter_tests WHERE id = {placeholder}", (rec_false.id,))
        assert raw_false["custom_bool"] == "no"

        # Verify that reading it back converts it to False
        found_false = TypeAdapterTest.find_one(rec_false.id)
        assert found_false.custom_bool is False

    def test_optional_annotated_custom_adapter(self, type_adapter_fixtures):
        """Tests an Optional field that also has a custom annotated adapter."""
        TypeAdapterTest = type_adapter_fixtures
        # Test with True
        rec_true = TypeAdapterTest(name="opt_custom_true", custom_bool=False, optional_custom_bool=True)
        rec_true.save()
        found_true = TypeAdapterTest.find_one(rec_true.id)
        assert found_true.optional_custom_bool is True
        placeholder = TypeAdapterTest.backend().dialect.get_placeholder()
        raw_true = TypeAdapterTest.backend().fetch_one(f"SELECT optional_custom_bool FROM type_adapter_tests WHERE id = {placeholder}", (rec_true.id,))
        assert raw_true["optional_custom_bool"] == "yes"

        # Test with False
        rec_false = TypeAdapterTest(name="opt_custom_false", custom_bool=False, optional_custom_bool=False)
        rec_false.save()
        found_false = TypeAdapterTest.find_one(rec_false.id)
        assert found_false.optional_custom_bool is False
        raw_false = TypeAdapterTest.backend().fetch_one(f"SELECT optional_custom_bool FROM type_adapter_tests WHERE id = {placeholder}", (rec_false.id,))
        assert raw_false["optional_custom_bool"] == "no"

        # Test with None
        rec_none = TypeAdapterTest(name="opt_custom_none", custom_bool=False, optional_custom_bool=None)
        rec_none.save()
        found_none = TypeAdapterTest.find_one(rec_none.id)
        assert found_none.optional_custom_bool is None
        raw_none = TypeAdapterTest.backend().fetch_one(f"SELECT optional_custom_bool FROM type_adapter_tests WHERE id = {placeholder}", (rec_none.id,))
        assert raw_none["optional_custom_bool"] is None

