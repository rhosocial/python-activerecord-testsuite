# src/rhosocial/activerecord/testsuite/feature/basic/expressions/test_expressions_async.py
"""Field expression contracts X1-X6 (async half, README section 12).

Mirrors ``test_expressions.py`` method for method. The ``.c`` accessor is a
class-level expression builder, so a test being ``async def`` changes only how
pytest schedules it: no await happens here and no connection is opened. The
async twins in ``TWINS`` are the models that declare ``FieldProxy`` for the
mapped-model checks, so both halves inspect the same declarations.
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

    def suggest_column_types(self):
        return self._table


class TestAsyncExpressions:
    """X1-X6 for column expressions on the borrowed fixture models."""

    @pytest.mark.parametrize("family,key,model_name,field", X1_CASES)
    async def test_x1_column_class_comes_from_declaration(
        self, expression_models, dialect, family, key, model_name, field
    ):
        """X1: the class is the dialect's answer, not a hard-coded constant."""
        table = dialect.suggest_column_types()
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
    async def test_x2_family_operation_renders(self, dialect, family, key, kind):
        """X2: one renderable operation per value family, DB-free."""
        column_class = column_class_for(dialect, key, family)
        column = column_class(dialect, "probe")
        expression = positive_expression(kind, column, dialect)

        assert callable(expression.to_sql)
        sql, _params = expression.to_sql()
        assert sql, "{} 的 {} 运算没有渲染出 SQL".format(family, kind)

    async def test_x3_json_column_has_no_like(self, dialect):
        """X3: a JSON document is not text; the operation must not exist."""
        column = JSONColumn(dialect, "payload")
        assert not hasattr(column, "like")
        with pytest.raises(AttributeError):
            column.like("%probe%")

    async def test_x3_xml_column_is_not_comparable(self, dialect):
        """X3: XML comparison is refused in Python, not by a database error."""
        column = XMLColumn(dialect, "markup")
        assert ComparisonMixin not in type(column).__mro__
        with pytest.raises(AttributeError):
            operator.eq(column, Literal(dialect, "<a/>"))
        with pytest.raises(AttributeError):
            operator.lt(column, Literal(dialect, "<b/>"))

    async def test_x4_use_column_expression_uses_column_name(self, expression_models, dialect):
        """X4: a renamed field produces the column name, not the field name."""
        model = next(item for item in expression_models if item.__name__ == "AsyncMappedUser")
        column = model.c.user_name

        assert column.name == "username"
        sql, _params = column.to_sql()
        assert dialect.format_identifier("username") in sql
        assert dialect.format_identifier("user_name") not in sql

    @pytest.mark.parametrize("field,sync_name,async_name", TWINS)
    async def test_x5_sync_async_same_column_class(
        self, expression_models, dialect, field, sync_name, async_name
    ):
        """X5: twins share one field mixin, so they resolve to the same class."""
        models = {item.__name__: item for item in expression_models}
        try:
            sync_column = getattr(models[sync_name].c, field)
            async_column = getattr(models[async_name].c, field)
        except ColumnTypeResolutionError as error:
            # A family the dialect stores through a substitute may have no
            # column class at all; that is an answered refusal, not a drift.
            pytest.skip("{} has no column class for {} ({})".format(dialect.name, field, error))

        assert type(sync_column) is type(async_column)
        assert sync_column.name == async_column.name
        assert sync_column.table == async_column.table

    async def test_x6_all_framework_keys_are_answered(self, dialect):
        """X6: a dialect that omits a framework key fails rather than skips."""
        table = dialect.suggest_column_types()
        missing = [
            getattr(key, "__name__", key) for key in FRAMEWORK_PYTHON_TYPES if key not in table
        ]
        assert not missing, "{} 漏答框架类型: {}".format(dialect.name, missing)

    async def test_x6_none_answer_skips_and_names_the_family(self):
        """X6: a present-but-None answer skips with the dialect and family named."""
        with pytest.raises(pytest.skip.Exception) as caught:
            column_class_for(_FakeDialect({int: None}), int, "integer")
        reason = str(caught.value)
        assert "FakeDialect" in reason
        assert "integer" in reason
        assert "没有运算类" in reason

    async def test_x6_missing_key_fails_instead_of_skipping(self):
        """X6: an unanswered key is a dialect gap, not an unsupported answer."""
        with pytest.raises(pytest.fail.Exception):
            column_class_for(_FakeDialect({}), int, "integer")
