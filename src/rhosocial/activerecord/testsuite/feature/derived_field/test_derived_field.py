# src/rhosocial/activerecord/testsuite/feature/derived_field/test_derived_field.py
import pytest

from rhosocial.activerecord.base import DerivedField
from rhosocial.activerecord.backend.expression import Column, Literal


class TestDerivedFieldDeclaration:

    def test_derived_fields_registered(self, product_class):
        assert "discounted_price" in product_class.__derived_fields__
        assert "total_value" in product_class.__derived_fields__

    def test_default_included_flag(self, product_class):
        assert product_class.__derived_fields__["discounted_price"].default_included is True
        assert product_class.__derived_fields__["total_value"].default_included is False

    def test_descriptor_class_access(self, product_class):
        assert isinstance(product_class.discounted_price, DerivedField)

    def test_derived_field_with_static_expression(self, product_class):
        """Test DerivedField constructed with a pre-built expression object (non-callable path)."""
        dialect = product_class.backend().dialect
        static_expr = Column(dialect, "price") * Literal(dialect, 2)
        df = DerivedField(static_expr)
        resolved = df.resolve(dialect)
        assert resolved is static_expr

    def test_descriptor_instance_default_none(self, product_class):
        p = product_class(name="x", price=10.0, quantity=1)
        assert p.discounted_price is None
        assert p.total_value is None

    def test_derived_field_names_mapping(self, product_class):
        names = product_class.__derived_field_names__
        df = product_class.__derived_fields__["discounted_price"]
        assert names[id(df)] == "discounted_price"


class TestDerivedFieldQuery:

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_find_all_derived_true(self, product_class):
        self._insert(product_class, "A", 100.0, 5)
        results = product_class.find_all(derived=True)
        assert len(results) == 1
        assert results[0].discounted_price == pytest.approx(90.0)
        assert results[0].total_value is None

    def test_find_all_derived_list_by_name(self, product_class):
        self._insert(product_class, "B", 50.0, 3)
        results = product_class.find_all(derived=["total_value"])
        assert len(results) == 1
        assert results[0].total_value == pytest.approx(150.0)
        assert results[0].discounted_price is None

    def test_find_all_derived_list_all(self, product_class):
        self._insert(product_class, "C", 200.0, 2)
        results = product_class.find_all(derived=["discounted_price", "total_value"])
        assert results[0].discounted_price == pytest.approx(180.0)
        assert results[0].total_value == pytest.approx(400.0)

    def test_find_one_derived(self, product_class):
        p = self._insert(product_class, "D", 80.0, 4)
        result = product_class.find_one(p.id, derived=True)
        assert result.discounted_price == pytest.approx(72.0)

    def test_find_all_derived_false_default(self, product_class):
        self._insert(product_class, "E", 60.0, 1)
        results = product_class.find_all()
        assert results[0].discounted_price is None
        assert results[0].total_value is None


class TestDerivedFieldFormA:
    """Tests for Form A declaration: ClassVar[DerivedField] = DerivedField(...)."""

    def test_form_a_fields_registered(self, product_form_a_class):
        assert "discounted_price" in product_form_a_class.__derived_fields__
        assert "total_value" in product_form_a_class.__derived_fields__

    def test_form_a_default_included(self, product_form_a_class):
        assert product_form_a_class.__derived_fields__["discounted_price"].default_included is True
        assert product_form_a_class.__derived_fields__["total_value"].default_included is False

    def test_form_a_query(self, product_form_a_class):
        p = product_form_a_class(name="FA", price=100.0, quantity=3)
        p.save()
        results = product_form_a_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0)

    def test_form_a_source_id_mapping(self, product_form_a_class):
        df = product_form_a_class.__derived_fields__["discounted_price"]
        assert df._source_id is not None
        assert product_form_a_class.__derived_field_names__[df._source_id] == "discounted_price"


class TestDerivedFieldDictForm:
    """Tests for derived=dict form."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_derived_dict_with_lambda(self, product_class):
        self._insert(product_class, "D1", 100.0, 4)
        results = product_class.find_all(
            derived={"my_discount": lambda d: Column(d, "price") * Literal(d, 0.8)}
        )
        assert results[0].__dict__["my_discount"] == pytest.approx(80.0)

    def test_derived_dict_with_derived_field_instance(self, product_class):
        self._insert(product_class, "D2", 50.0, 2)
        df = product_class.__derived_fields__["total_value"]
        results = product_class.find_all(
            derived={"tv": df}
        )
        assert results[0].__dict__["tv"] == pytest.approx(100.0)


    def test_derived_dict_with_expression_object(self, product_class):
        self._insert(product_class, "D3", 80.0, 5)
        dialect = product_class.backend().dialect
        expr = Column(dialect, "price") * Literal(dialect, 0.5)
        results = product_class.find_all(
            derived={"half_price": expr}
        )
        assert results[0].__dict__["half_price"] == pytest.approx(40.0)


class TestDerivedFieldLookupByInstance:
    """Tests for derived=[DerivedField instance] form."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_lookup_by_derived_field_instance(self, product_class):
        self._insert(product_class, "L1", 200.0, 1)
        df = product_class.__derived_fields__["discounted_price"]
        results = product_class.find_all(derived=[df])
        assert results[0].discounted_price == pytest.approx(180.0)


class TestExtraDerived:

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_extra_derived_basic(self, product_class):
        self._insert(product_class, "F", 100.0, 10)
        results = product_class.find_all(
            extra_derived={"triple_price": lambda d: Column(d, "price") * Literal(d, 3)}
        )
        assert len(results) == 1
        assert results[0].__dict__["triple_price"] == pytest.approx(300.0)

    def test_extra_derived_conflict_raises(self, product_class):
        self._insert(product_class, "G", 50.0, 2)
        with pytest.raises(ValueError, match="conflicts with a declared derived field"):
            product_class.find_all(
                extra_derived={"discounted_price": lambda d: Column(d, "price") * Literal(d, 0.5)}
            )

    def test_derived_and_extra_derived_together(self, product_class):
        self._insert(product_class, "H", 40.0, 5)
        results = product_class.find_all(
            derived=True,
            extra_derived={"double_qty": lambda d: Column(d, "quantity") * Literal(d, 2)}
        )
        assert results[0].discounted_price == pytest.approx(36.0)
        assert results[0].__dict__["double_qty"] == pytest.approx(10.0)


class TestDerivedFieldWithProxy:
    """Tests for DerivedField using FieldProxy in expressions."""

    def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        p.save()
        return p

    def test_proxy_derived_query(self, product_with_proxy_class):
        self._insert(product_with_proxy_class, "P1", 100.0, 4)
        results = product_with_proxy_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0)

    def test_proxy_derived_all_fields(self, product_with_proxy_class):
        self._insert(product_with_proxy_class, "P2", 200.0, 3)
        results = product_with_proxy_class.find_all(
            derived=["discounted_price", "total_value"]
        )
        assert results[0].discounted_price == pytest.approx(180.0)
        assert results[0].total_value == pytest.approx(600.0)

    def test_proxy_derived_not_in_model_fields(self, product_with_proxy_class):
        assert "discounted_price" not in product_with_proxy_class.model_fields
        assert "total_value" not in product_with_proxy_class.model_fields

    def test_proxy_derived_not_in_dirty_fields(self, product_with_proxy_class):
        self._insert(product_with_proxy_class, "P3", 50.0, 2)
        instance = product_with_proxy_class.find_all(derived=True)[0]
        instance.__dict__["discounted_price"] = 999.0
        assert "discounted_price" not in instance.dirty_fields

    def test_proxy_derived_read_only(self, product_with_proxy_class):
        self._insert(product_with_proxy_class, "P4", 80.0, 1)
        instance = product_with_proxy_class.find_all(derived=True)[0]
        with pytest.raises(AttributeError):
            instance.discounted_price = 123.0

    def test_proxy_derived_not_saved_to_db(self, product_with_proxy_class):
        p = self._insert(product_with_proxy_class, "P5", 60.0, 2)
        instance = product_with_proxy_class.find_one(p.id, derived=True)
        assert instance.discounted_price == pytest.approx(54.0)
        instance.name = "P5_modified"
        instance.save()
        fresh = product_with_proxy_class.find_one(p.id, derived=True)
        assert fresh.name == "P5_modified"
        assert fresh.discounted_price == pytest.approx(54.0)
