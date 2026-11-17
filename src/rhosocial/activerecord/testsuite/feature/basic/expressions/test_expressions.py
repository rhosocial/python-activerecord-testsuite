# src/rhosocial/activerecord/testsuite/feature/basic/expressions/test_expressions.py
"""Field expression contracts X1-X6 (sync half, README section 12).

Every assertion is DB-free: it reads the dialect's static column-class answer,
builds an expression tree, and checks rendered SQL. No table is created and no
connection is opened, so this half runs beside the other ``basic`` groups.

The classes under test are the ones already declared by ``types_models``,
``types_complex_models`` and ``user_models``; only their ``.c`` expressions are
inspected. A pass means the model-declaration -> dialect-answer -> operation
route is intact, not that a particular backend class was hard-coded.
"""

import operator

import pytest
from rhosocial.activerecord.backend.expression import JSONColumn, Literal, XMLColumn
from rhosocial.activerecord.backend.expression.mixins import ComparisonMixin
from rhosocial.activerecord.base.field_proxy import ColumnTypeResolutionError
from rhosocial.activerecord.base.framework_types import FRAMEWORK_PYTHON_TYPES

from rhosocial.activerecord.testsuite.feature.basic.expressions.expression_support import (
    OPERATIONS,
    TWINS,
    X1_CASES,
    column_class_for,
    positive_expression,
)


class _FakeDialect:
    """A dialect whose column-class table is supplied by the X6 unit cases."""

    name = "FakeDialect"

    def __init__(self, table):
        self._table = table

    def suggested_column_types(self):
        return self._table


class TestExpressions:
    """X1-X6 for column expressions on the borrowed fixture models."""

    @pytest.mark.parametrize("family,key,model_name,field", X1_CASES)
    def test_x1_column_class_comes_from_declaration(
        self, expression_models, dialect, family, key, model_name, field
    ):
        """X1: the class is the dialect's answer, not a hard-coded constant."""
        table = dialect.suggested_column_types()
        assert key in table, "{} 漏答 {}（键 {!r}）".format(dialect.name, family, key)
        expected = table[key]
        model = next(item for item in expression_models if item.__name__ == model_name)
        if expected is None:
            # E-2: the value can be stored but no operation class exists, so the
            # accessor refuses explicitly instead of silently using a base class.
            with pytest.raises(ColumnTypeResolutionError):
                getattr(model.c, field)
            return
        assert type(getattr(model.c, field)) is expected

    @pytest.mark.parametrize("family,key,kind", OPERATIONS)
    def test_x2_family_operation_renders(self, dialect, family, key, kind):
        """X2: one renderable operation per value family, DB-free."""
        column_class = column_class_for(dialect, key, family)
        column = column_class(dialect, "probe")
        expression = positive_expression(kind, column, dialect)

        assert callable(expression.to_sql)
        sql, _params = expression.to_sql()
        assert sql, "{} 的 {} 运算没有渲染出 SQL".format(family, kind)

    def test_x3_json_column_has_no_like(self, dialect):
        """X3: a JSON document is not text; the operation must not exist."""
        column = JSONColumn(dialect, "payload")
        assert not hasattr(column, "like")
        with pytest.raises(AttributeError):
            column.like("%probe%")

    def test_x3_xml_column_is_not_comparable(self, dialect):
        """X3: XML comparison is refused in Python, not by a database error."""
        column = XMLColumn(dialect, "markup")
        assert ComparisonMixin not in type(column).__mro__
        with pytest.raises(AttributeError):
            operator.eq(column, Literal(dialect, "<a/>"))
        with pytest.raises(AttributeError):
            operator.lt(column, Literal(dialect, "<b/>"))

    def test_x4_use_column_expression_uses_column_name(self, expression_models, dialect):
        """X4: a renamed field produces the column name, not the field name."""
        model = next(item for item in expression_models if item.__name__ == "AsyncMappedUser")
        column = model.c.user_name

        assert column.name == "username"
        sql, _params = column.to_sql()
        assert dialect.format_identifier("username") in sql
        assert dialect.format_identifier("user_name") not in sql

    @pytest.mark.parametrize("field,sync_name,async_name", TWINS)
    def test_x5_sync_async_same_column_class(
        self, expression_models, dialect, field, sync_name, async_name
    ):
        """X5: twins share one field mixin, so they resolve to the same class."""
        models = {item.__name__: item for item in expression_models}
        sync_column = getattr(models[sync_name].c, field)
        async_column = getattr(models[async_name].c, field)

        assert type(sync_column) is type(async_column)
        assert sync_column.name == async_column.name
        assert sync_column.table == async_column.table

    def test_x6_all_framework_keys_are_answered(self, dialect):
        """X6: a dialect that omits a framework key fails rather than skips."""
        table = dialect.suggested_column_types()
        missing = [
            getattr(key, "__name__", key) for key in FRAMEWORK_PYTHON_TYPES if key not in table
        ]
        assert not missing, "{} 漏答框架类型: {}".format(dialect.name, missing)

    def test_x6_none_answer_skips_and_names_the_family(self):
        """X6: a present-but-None answer skips with the dialect and family named."""
        with pytest.raises(pytest.skip.Exception) as caught:
            column_class_for(_FakeDialect({int: None}), int, "integer")
        reason = str(caught.value)
        assert "FakeDialect" in reason
        assert "integer" in reason
        assert "没有运算类" in reason

    def test_x6_missing_key_fails_instead_of_skipping(self):
        """X6: an unanswered key is a dialect gap, not an unsupported answer."""
        with pytest.raises(pytest.fail.Exception):
            column_class_for(_FakeDialect({}), int, "integer")
