# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_derived_field.py
"""Tests for DerivedField declaration, registration, and query-time evaluation."""
import pytest
from typing import ClassVar, Optional
from typing_extensions import Annotated

from rhosocial.activerecord.base import DerivedField, UseColumn
from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.backend.expression import Column, Literal


class TestDerivedFieldDeclaration:
    """Test derived field declaration and registration metadata."""

    def test_derived_fields_registered(self, product_class):
        """Declared DerivedField names should appear in __derived_fields__."""
        assert "discounted_price" in product_class.__derived_fields__, \
            "Expected 'discounted_price' to be registered"
        assert "total_value" in product_class.__derived_fields__, \
            "Expected 'total_value' to be registered"

    def test_descriptor_class_access(self, product_class):
        """Accessing a derived field by class should return a DerivedField descriptor."""
        assert isinstance(product_class.discounted_price, DerivedField), \
            "Expected class-level access to return a DerivedField instance"

    def test_derived_field_with_static_expression(self, product_class):
        """Test DerivedField constructed with a pre-built expression object (non-callable path)."""
        dialect = product_class.backend().dialect
        static_expr = Column(dialect, "price") * Literal(dialect, 2)
        df = DerivedField(static_expr)
        resolved = df.resolve(dialect)
        assert resolved is static_expr, \
            "Expected a static expression to be returned unchanged by resolve()"

    def test_descriptor_instance_default_none(self, product_class):
        """Derived fields should default to None on a fresh instance."""
        p = product_class(name="x", price=10.0, quantity=1)
        assert p.discounted_price is None, "Expected discounted_price to default to None"
        assert p.total_value is None, "Expected total_value to default to None"

    def test_derived_field_names_mapping(self, product_class):
        """__derived_field_names__ should map id(field) to the field name."""
        names = product_class.__derived_field_names__
        df = product_class.__derived_fields__["discounted_price"]
        assert names[id(df)] == "discounted_price", \
            "Expected id(df) to map back to 'discounted_price'"


class TestDerivedFieldQuery:
    """Test derived field evaluation under find_all/find_one with the derived argument."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_find_all_derived_true(self, product_class):
        """find_all(derived=True) should populate all declared derived fields."""
        self._insert(product_class, "A", 100.0, 5)
        results = product_class.find_all(derived=True)
        assert len(results) == 1, "Expected 1 record to be returned"
        assert results[0].discounted_price == pytest.approx(90.0), \
            "Expected discounted_price to be 90.0"
        assert results[0].total_value == pytest.approx(500.0), \
            "Expected total_value to be 500.0"

    def test_find_all_derived_list_by_name(self, product_class):
        """find_all(derived=[name]) should populate only the listed derived fields."""
        self._insert(product_class, "B", 50.0, 3)
        results = product_class.find_all(derived=["total_value"])
        assert len(results) == 1, "Expected 1 record to be returned"
        assert results[0].total_value == pytest.approx(150.0), \
            "Expected total_value to be 150.0"
        assert results[0].discounted_price is None, \
            "Expected discounted_price to remain None"

    def test_find_all_derived_list_all(self, product_class):
        """find_all with an explicit list of derived names should populate those fields."""
        self._insert(product_class, "C", 200.0, 2)
        results = product_class.find_all(derived=["discounted_price", "total_value"])
        assert results[0].discounted_price == pytest.approx(180.0), \
            "Expected discounted_price to be 180.0"
        assert results[0].total_value == pytest.approx(400.0), \
            "Expected total_value to be 400.0"

    def test_find_one_derived(self, product_class):
        """find_one(derived=True) should populate declared derived fields."""
        p = self._insert(product_class, "D", 80.0, 4)
        result = product_class.find_one(p.id, derived=True)
        assert result.discounted_price == pytest.approx(72.0), \
            "Expected discounted_price to be 72.0"

    def test_find_one_or_fail_derived(self, product_class):
        """find_one_or_fail(derived=True) should populate declared derived fields."""
        p = self._insert(product_class, "D2", 80.0, 4)
        result = product_class.find_one_or_fail(p.id, derived=True)
        assert result.discounted_price == pytest.approx(72.0), \
            "Expected discounted_price to be 72.0"
        assert result.total_value == pytest.approx(320.0), "Expected total_value to be 320.0"

    def test_find_one_or_fail_derived_list(self, product_class):
        """find_one_or_fail with a derived list should populate only those fields."""
        p = self._insert(product_class, "D3", 80.0, 4)
        result = product_class.find_one_or_fail(p.id, derived=["discounted_price", "total_value"])
        assert result.discounted_price == pytest.approx(72.0), \
            "Expected discounted_price to be 72.0"
        assert result.total_value == pytest.approx(320.0), "Expected total_value to be 320.0"

    def test_find_all_derived_false_default(self, product_class):
        """Without the derived argument, derived fields should remain None."""
        self._insert(product_class, "E", 60.0, 1)
        results = product_class.find_all()
        assert results[0].discounted_price is None, \
            "Expected discounted_price to remain None"
        assert results[0].total_value is None, "Expected total_value to remain None"

    def test_find_all_derived_all(self, product_class):
        """find_all(derived='all') should populate all declared derived fields."""
        self._insert(product_class, "F", 100.0, 5)
        results = product_class.find_all(derived="all")
        assert len(results) == 1, "Expected 1 record to be returned"
        assert results[0].discounted_price == pytest.approx(90.0), \
            "Expected discounted_price to be 90.0"
        assert results[0].total_value == pytest.approx(500.0), \
            "Expected total_value to be 500.0"

    def test_find_one_derived_all(self, product_class):
        """find_one(derived='all') should populate all declared derived fields."""
        p = self._insert(product_class, "G", 80.0, 4)
        result = product_class.find_one(p.id, derived="all")
        assert result.discounted_price == pytest.approx(72.0), \
            "Expected discounted_price to be 72.0"
        assert result.total_value == pytest.approx(320.0), "Expected total_value to be 320.0"

    def test_find_one_or_fail_derived_all(self, product_class):
        """find_one_or_fail(derived='all') should populate all declared derived fields."""
        p = self._insert(product_class, "H", 60.0, 3)
        result = product_class.find_one_or_fail(p.id, derived="all")
        assert result.discounted_price == pytest.approx(54.0), \
            "Expected discounted_price to be 54.0"
        assert result.total_value == pytest.approx(180.0), "Expected total_value to be 180.0"


class TestDerivedFieldFormA:
    """Tests for Form A declaration: ClassVar[DerivedField] = DerivedField(...)."""

    def test_form_a_fields_registered(self, product_form_a_class):
        """Form A derived fields should be registered under __derived_fields__."""
        assert "discounted_price" in product_form_a_class.__derived_fields__, \
            "Expected 'discounted_price' to be registered for Form A"
        assert "total_value" in product_form_a_class.__derived_fields__, \
            "Expected 'total_value' to be registered for Form A"

    def test_form_a_query(self, product_form_a_class):
        """Form A derived fields should be evaluable through find_all(derived=True)."""
        p = product_form_a_class(name="FA", price=100.0, quantity=3)
        p.save()
        results = product_form_a_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0), \
            "Expected discounted_price to be 90.0"
        assert results[0].total_value == pytest.approx(300.0), \
            "Expected total_value to be 300.0"

    def test_form_a_source_id_mapping(self, product_form_a_class):
        """Form A derived fields should expose a _source_id and name mapping entry."""
        df = product_form_a_class.__derived_fields__["discounted_price"]
        assert df._source_id is not None, "Expected _source_id to be populated"
        assert product_form_a_class.__derived_field_names__[df._source_id] == "discounted_price", \
            "Expected the name mapping to point back to 'discounted_price'"


class TestDerivedFieldDictForm:
    """Tests for derived=dict form."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_derived_dict_with_lambda(self, product_class):
        """A lambda-based derived dict should evaluate against the dialect."""
        self._insert(product_class, "D1", 100.0, 4)
        results = product_class.find_all(
            derived={"my_discount": lambda d: Column(d, "price") * Literal(d, 0.8)}
        )
        assert results[0].__dict__["my_discount"] == pytest.approx(80.0), \
            "Expected my_discount to be 80.0"

    def test_derived_dict_with_derived_field_instance(self, product_class):
        """A derived dict should accept a pre-registered DerivedField instance."""
        self._insert(product_class, "D2", 50.0, 2)
        df = product_class.__derived_fields__["total_value"]
        results = product_class.find_all(
            derived={"tv": df}
        )
        assert results[0].__dict__["tv"] == pytest.approx(100.0), \
            "Expected tv to be 100.0"


    def test_derived_dict_with_expression_object(self, product_class):
        """A derived dict should accept a pre-built expression object directly."""
        self._insert(product_class, "D3", 80.0, 5)
        dialect = product_class.backend().dialect
        expr = Column(dialect, "price") * Literal(dialect, 0.5)
        results = product_class.find_all(
            derived={"half_price": expr}
        )
        assert results[0].__dict__["half_price"] == pytest.approx(40.0), \
            "Expected half_price to be 40.0"


class TestDerivedFieldLookupByInstance:
    """Tests for derived=[DerivedField instance] form."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_lookup_by_derived_field_instance(self, product_class):
        """derived=[DerivedField instance] should populate the requested field."""
        self._insert(product_class, "L1", 200.0, 1)
        df = product_class.__derived_fields__["discounted_price"]
        results = product_class.find_all(derived=[df])
        assert results[0].discounted_price == pytest.approx(180.0), \
            "Expected discounted_price to be 180.0"


class TestExtraDerived:
    """Tests for the extra_derived argument."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_extra_derived_basic(self, product_class):
        """extra_derived should add new derived fields without disturbing declared ones."""
        self._insert(product_class, "F", 100.0, 10)
        results = product_class.find_all(
            extra_derived={"triple_price": lambda d: Column(d, "price") * Literal(d, 3)}
        )
        assert len(results) == 1, "Expected 1 record to be returned"
        assert results[0].__dict__["triple_price"] == pytest.approx(300.0), \
            "Expected triple_price to be 300.0"

    def test_extra_derived_conflict_raises(self, product_class):
        """extra_derived must reject names that conflict with declared derived fields."""
        self._insert(product_class, "G", 50.0, 2)
        with pytest.raises(ValueError, match="conflicts with a declared derived field"):
            product_class.find_all(
                extra_derived={"discounted_price": lambda d: Column(d, "price") * Literal(d, 0.5)}
            )

    def test_derived_and_extra_derived_together(self, product_class):
        """derived and extra_derived should compose in a single query."""
        self._insert(product_class, "H", 40.0, 5)
        results = product_class.find_all(
            derived=True,
            extra_derived={"double_qty": lambda d: Column(d, "quantity") * Literal(d, 2)}
        )
        assert results[0].discounted_price == pytest.approx(36.0), \
            "Expected discounted_price to be 36.0"
        assert results[0].total_value == pytest.approx(200.0), \
            "Expected total_value to be 200.0"
        assert results[0].__dict__["double_qty"] == pytest.approx(10.0), \
            "Expected double_qty to be 10.0"


class TestDerivedFieldWithProxy:
    """Tests for DerivedField using FieldProxy in expressions."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_proxy_derived_query(self, product_with_proxy_class):
        """FieldProxy-backed derived fields should evaluate via find_all(derived=True)."""
        self._insert(product_with_proxy_class, "P1", 100.0, 4)
        results = product_with_proxy_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0), \
            "Expected discounted_price to be 90.0"
        assert results[0].total_value == pytest.approx(400.0), \
            "Expected total_value to be 400.0"

    def test_proxy_derived_all_fields(self, product_with_proxy_class):
        """FieldProxy-backed derived fields should support an explicit list of names."""
        self._insert(product_with_proxy_class, "P2", 200.0, 3)
        results = product_with_proxy_class.find_all(
            derived=["discounted_price", "total_value"]
        )
        assert results[0].discounted_price == pytest.approx(180.0), \
            "Expected discounted_price to be 180.0"
        assert results[0].total_value == pytest.approx(600.0), \
            "Expected total_value to be 600.0"

    def test_proxy_derived_not_in_model_fields(self, product_with_proxy_class):
        """Derived fields must not appear in model_fields (they are not regular fields)."""
        assert "discounted_price" not in product_with_proxy_class.model_fields, \
            "Expected 'discounted_price' not to be in model_fields"
        assert "total_value" not in product_with_proxy_class.model_fields, \
            "Expected 'total_value' not to be in model_fields"

    def test_proxy_derived_not_in_dirty_fields(self, product_with_proxy_class):
        """Mutating a derived field must not mark it dirty."""
        self._insert(product_with_proxy_class, "P3", 50.0, 2)
        instance = product_with_proxy_class.find_all(derived=True)[0]
        instance.__dict__["discounted_price"] = 999.0
        assert "discounted_price" not in instance.dirty_fields, \
            "Expected 'discounted_price' not to be in dirty_fields"

    def test_proxy_derived_read_only(self, product_with_proxy_class):
        """Assigning to a derived attribute must raise AttributeError."""
        self._insert(product_with_proxy_class, "P4", 80.0, 1)
        instance = product_with_proxy_class.find_all(derived=True)[0]
        with pytest.raises(AttributeError):
            instance.discounted_price = 123.0

    def test_proxy_derived_not_saved_to_db(self, product_with_proxy_class):
        """Derived values must not be persisted on save."""
        p = self._insert(product_with_proxy_class, "P5", 60.0, 2)
        instance = product_with_proxy_class.find_one(p.id, derived=True)
        assert instance.discounted_price == pytest.approx(54.0), \
            "Expected discounted_price to be 54.0"
        instance.name = "P5_modified"
        instance.save()
        fresh = product_with_proxy_class.find_one(p.id, derived=True)
        assert fresh.name == "P5_modified", "Expected the persisted name to be updated"
        assert fresh.discounted_price == pytest.approx(54.0), \
            "Expected derived price to remain unchanged after save"


class TestDerivedFieldWithUseColumnAndAdapter:
    """Tests for DerivedField with UseColumn and UseAdapter annotations."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_use_column_alias_in_select(self, product_with_column_and_adapter_class):
        """UseColumn controls the SELECT alias; result maps back to Python field name."""
        self._insert(product_with_column_and_adapter_class, "UC1", 100.0, 5)
        results = product_with_column_and_adapter_class.find_all(derived=True)
        # discounted_price has UseColumn("disc") — alias is "disc" in SQL,
        # but the value is accessible via the Python attribute name
        assert results[0].discounted_price == pytest.approx(90.0), \
            "Expected discounted_price to be 90.0"
        assert results[0].total_int == 500, "Expected total_int to be 500"

    def test_use_adapter_from_database(self, product_with_column_and_adapter_class):
        """UseAdapter applies from_database conversion on the derived field value."""
        self._insert(product_with_column_and_adapter_class, "UA1", 33.3, 3)
        results = product_with_column_and_adapter_class.find_all(derived=["total_int"])
        # 33.3 * 3 = 99.9, adapter rounds to int → 100
        assert results[0].total_int == 100, "Expected total_int to be rounded to 100"
        assert isinstance(results[0].total_int, int), "Expected total_int to be an int"

    def test_use_column_field_not_in_model_fields(self, product_with_column_and_adapter_class):
        """Derived fields should not be exposed as regular model fields."""
        assert "discounted_price" not in product_with_column_and_adapter_class.model_fields, \
            "Expected 'discounted_price' not to be in model_fields"
        assert "total_int" not in product_with_column_and_adapter_class.model_fields, \
            "Expected 'total_int' not to be in model_fields"

    def test_use_column_column_name_stored(self, product_with_column_and_adapter_class):
        """UseColumn annotation should be recorded as column_name on the descriptor."""
        df = product_with_column_and_adapter_class.__derived_fields__["discounted_price"]
        assert df.column_name == "disc", "Expected column_name to be 'disc'"

    def test_use_adapter_stored(self, product_with_column_and_adapter_class):
        """UseAdapter annotation should be recorded as adapter on the descriptor."""
        df = product_with_column_and_adapter_class.__derived_fields__["total_int"]
        assert df.adapter is not None, "Expected the adapter to be stored on the descriptor"

    def test_use_column_and_adapter_together(self, product_with_column_and_adapter_class):
        """Both UseColumn and UseAdapter can coexist on the same derived field."""
        self._insert(product_with_column_and_adapter_class, "CA1", 50.0, 4)
        results = product_with_column_and_adapter_class.find_all(
            derived=["discounted_price", "total_int"]
        )
        assert results[0].discounted_price == pytest.approx(45.0), \
            "Expected discounted_price to be 45.0"
        assert results[0].total_int == 200, "Expected total_int to be 200"


class TestDerivedFieldColumnConflict:
    """Tests that column name conflicts between regular and derived fields are detected."""

    def test_use_column_conflict_raises(self):
        """UseColumn on derived field must not duplicate a regular field's column name."""
        with pytest.raises(TypeError, match="conflicts with a regular field's column name"):
            class ConflictModel(ActiveRecord):
                __table_name__ = "conflict"
                id: Optional[int] = None
                discount_rate: Annotated[float, UseColumn("disc")]
                discounted: ClassVar[Annotated[float, DerivedField(
                    lambda d: Column(d, "price") * Literal(d, 0.9),
                ), UseColumn("disc")]]

    def test_use_column_no_conflict_different_names(self):
        """Different column names should not conflict."""
        class NoConflict(ActiveRecord):
            __table_name__ = "no_conflict"
            id: Optional[int] = None
            discount_rate: Annotated[float, UseColumn("rate")]
            discounted: ClassVar[Annotated[float, DerivedField(
                lambda d: Column(d, "price") * Literal(d, 0.9),
            ), UseColumn("disc")]]

        assert NoConflict.__derived_fields__["discounted"].column_name == "disc", \
            "Expected the descriptor's column_name to be 'disc'"
