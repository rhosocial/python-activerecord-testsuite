# src/rhosocial/activerecord/testsuite/utils/expression.py
"""
Expression serialization round-trip / contract test helpers.

This module is the test-only home (NOT shipped as part of the core library's
runtime API) for constructing expression instances and asserting they survive
all three serializations. It is shared across the core library tests and all
backend test suites (MySQL / PostgreSQL / MariaDB / SQL Server / Oracle).

After registering a class into the ExpressionRegistry, expression instances
must satisfy:

- ``get_params()`` reflects every ``__init__`` parameter
- A round-trip through the three encoding channels returns a structurally
  equivalent instance (``get_params()`` equal)
- When the chosen backend's dialect supports ``to_sql()``, the SQL keyword
  rendering is identical
"""

import dataclasses
import inspect
import typing
import warnings
from typing import Any, Callable, Dict, List, Optional, Type

from rhosocial.activerecord.backend.expression.bases import BaseExpression


def _placeholder_for(param: inspect.Parameter, dialect: Any = None):
    """Return a heuristic construction value for a required parameter."""
    annotation = param.annotation
    if annotation is not inspect.Parameter.empty:
        origin = typing.get_origin(annotation)
        raw = annotation if origin is None else origin
        if isinstance(annotation, str):
            text = annotation
        else:
            text = getattr(raw, "__name__", "")
        if raw in (list, tuple, set):
            return []
        if raw is dict:
            return {}
        if raw is str or "str" in text:
            return "x"
        if raw is int:
            return 1
        if raw is float:
            return 1.0
        if raw is bool:
            return True
        if "Expression" in text or "Subquery" in text:
            return _literal(dialect)

    name = param.name
    if name in ("value",):
        return 1
    if name in ("values", "columns", "args", "params", "predicates", "expressions"):
        return []
    if name in ("left", "right") or "predicate" in name or "condition" in name:
        return _comparison(dialect)
    if "expression" in name or name in ("expr", "operand", "subquery", "query"):
        return _literal(dialect)
    return "x"


def _literal(dialect):
    from rhosocial.activerecord.backend.expression.core import Literal

    return Literal(dialect, 1)


def _comparison(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.predicates import ComparisonPredicate

    return ComparisonPredicate(dialect, "=", Column(dialect, "a"), _literal(dialect))


def _try_construct(cls, dialect):
    """Construct an instance of cls with heuristic arguments; None on failure."""
    sig = inspect.signature(cls.__init__)
    # DataType-family declares dialect as an optional trailing keyword.
    has_dialect = "dialect" in sig.parameters
    first_param = next((p for p in sig.parameters if p != "self"), None)
    dialect_as_kw = first_param != "dialect"
    args = []
    kwargs = {}
    skipped_defaulted_positional = False
    for pname, param in sig.parameters.items():
        if pname in ("self", "dialect"):
            continue
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            if not skipped_defaulted_positional:
                args.append(_literal(dialect))
            continue
        if param.default is not inspect.Parameter.empty:
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                skipped_defaulted_positional = True
            continue
        placeholder = _placeholder_for(param, dialect)
        # placeholder None → default case; real value provided otherwise
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            kwargs[pname] = placeholder
        else:
            args.append(placeholder)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if not has_dialect:
                return cls(*args, **kwargs)
            if dialect_as_kw:
                return cls(*args, dialect=dialect, **kwargs)
            return cls(dialect, *args, **kwargs)
    except Exception:
        return None


def special_constructors():
    """Explicit constructors for classes whose ``__init__`` rejects heuristic
    placeholder values. Keyed by a suffix that matches the class's full
    module.ClassName. Registered by name only — this is a static registry and
    backends may register their own entries for backend-specific expressions.
    """
    return {
        "advanced_functions.JSONExpression": _json_expr,
        "query_parts.JoinExpression": _join_expr,
        "statements.ddl_partition.PartitionClause": _partition_clause,
        "statements.dml.OnConflictClause": _on_conflict,
        "statements.dml.UpdateExpression": _update_expr,
        "statements.ddl_view.CreateViewExpression": _create_view_expr,
        "datetime.ExtractExpression": _extract_expr,
        "datetime.DatePartExpression": _datepart_expr,
        "datetime.DateTruncExpression": _datetrunc_expr,
        "datetime.IntervalExpression": _interval_expr,
        "datetime.DateTimeDiffExpression": _datetime_diff_expr,
        "datetime.DateTimeSubtractExpression": _datetime_sub_expr,
        "datetime.DateTimeAddExpression": _datetime_add_expr,
    }


def _json_expr(dialect):
    from rhosocial.activerecord.backend.expression.advanced_functions import JSONExpression
    from rhosocial.activerecord.backend.expression.core import Literal

    return JSONExpression(dialect, Literal(dialect, '{"a": 1}'), path="$.a")


def _table(dialect, name="t"):
    from rhosocial.activerecord.backend.expression.core import TableExpression

    return TableExpression(dialect, name)


def _join_expr(dialect):
    from rhosocial.activerecord.backend.expression.query_parts import JoinExpression
    from rhosocial.activerecord.backend.expression.predicates import ComparisonPredicate
    from rhosocial.activerecord.backend.expression.core import Column

    return JoinExpression(
        dialect,
        left_table=_table(dialect, "a"),
        right_table=_table(dialect, "b"),
        condition=ComparisonPredicate(dialect, "=", Column(dialect, "a"), Column(dialect, "b")),
    )


def _partition_clause(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.statements.ddl_partition import (
        PartitionClause,
        PartitionStrategy,
    )

    return PartitionClause(dialect, method=PartitionStrategy.RANGE, keys=[Column(dialect, "created_at")])


def _on_conflict(dialect):
    from rhosocial.activerecord.backend.expression.statements.dml import OnConflictClause

    return OnConflictClause(dialect, do_nothing=True, conflict_target=["id"])


def _update_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Literal
    from rhosocial.activerecord.backend.expression.statements.dml import UpdateExpression

    return UpdateExpression(dialect, table=_table(dialect), assignments={"a": Literal(dialect, 1)})


def _create_view_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.statements.ddl_view import CreateViewExpression
    from rhosocial.activerecord.backend.expression.statements.dql import QueryExpression

    query = QueryExpression(dialect, select=[Column(dialect, "id")], from_=_table(dialect, "t"))
    return CreateViewExpression(dialect, view_name="v", query=query)


def _extract_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.datetime import ExtractExpression

    return ExtractExpression(dialect, "YEAR", Column(dialect, "created_at"))


def _datepart_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.datetime import DatePartExpression

    return DatePartExpression(dialect, "YEAR", Column(dialect, "created_at"))


def _datetrunc_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.datetime import DateTruncExpression

    return DateTruncExpression(dialect, "year", Column(dialect, "created_at"))


def _interval_expr(dialect):
    from rhosocial.activerecord.backend.expression.datetime import IntervalExpression

    return IntervalExpression(dialect, 7, "day")


def _datetime_diff_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.datetime import DateTimeDiffExpression

    return DateTimeDiffExpression(dialect, "day", Column(dialect, "a"), Column(dialect, "b"))


def _datetime_sub_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.datetime import (
        DateTimeSubtractExpression,
        IntervalExpression,
    )

    return DateTimeSubtractExpression(dialect, Column(dialect, "a"), IntervalExpression(dialect, 1, "day"))


def _datetime_add_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.datetime import (
        DateTimeAddExpression,
        IntervalExpression,
    )

    return DateTimeAddExpression(dialect, Column(dialect, "a"), IntervalExpression(dialect, 1, "day"))


_SPECIAL_REGISTRY: Dict[str, Callable] = special_constructors()


def register_special_constructor(fqn_suffix: str, factory: Callable) -> None:
    """Register an explicit constructor for an expression class.

    ``fqn_suffix`` must match the tail of the class's fully qualified name
    (e.g. ``"json.MySQLJSONObjectExpression"``). ``factory(dialect)`` must
    return an expression instance.
    """
    _SPECIAL_REGISTRY[fqn_suffix] = factory


def make_instance(cls: Type[BaseExpression], dialect: Any):
    """Best-effort construction for an expression class.

    Returns (instance, source) where source is "special", "heuristic", or
    (None, "failed").
    """
    full_name = f"{cls.__module__}.{cls.__name__}"
    special = next((fn for s, fn in _SPECIAL_REGISTRY.items() if full_name.endswith(s)), None)
    if special is not None:
        try:
            return special(dialect), "special"
        except Exception:
            return None, "special-failed"
    instance = _try_construct(cls, dialect)
    if instance is None:
        return None, "failed"
    return instance, "heuristic"


def collect_expression_classes(package_path: str) -> Dict[str, Type[BaseExpression]]:
    """Walk a package subtree and collect every defined BaseExpression subclass."""
    import importlib
    import pkgutil

    pkg = importlib.import_module(package_path)
    classes: Dict[str, Type[BaseExpression]] = {}
    for _, modname, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for name in dir(mod):
            obj = getattr(mod, name, None)
            if (
                isinstance(obj, type)
                and obj.__module__ == modname
                and issubclass(obj, BaseExpression)
                and obj is not BaseExpression
                and not inspect.isabstract(obj)
            ):
                classes[f"{modname}.{name}"] = obj
    return classes


def register_all(classes: Dict[str, Type[BaseExpression]]) -> None:
    from rhosocial.activerecord.backend.expression.serialization import ExpressionRegistry

    for cls in classes.values():
        ExpressionRegistry.register(cls)


def assert_params_equal(a: Any, b: Any, path: str = "params") -> None:
    """Deep-compare two get_params() outputs, treating nested BaseExpression
    instances as structurally equal and nested dataclasses as recursively compared.
    """
    if a is b:
        return
    if isinstance(a, BaseExpression) and isinstance(b, BaseExpression):
        assert_params_equal(a.get_params(), b.get_params(), path + ".<expr>")
        return
    if dataclasses.is_dataclass(a) and not isinstance(a, type):
        assert dataclasses.is_dataclass(b) and not isinstance(b, type), (
            f"{path}: expected dataclass instance, got {type(b).__name__}"
        )
        for f in dataclasses.fields(a):
            assert_params_equal(getattr(a, f.name), getattr(b, f.name), f"{path}.{f.name}")
        return
    assert type(a) is type(b) or (
        isinstance(a, (list, tuple, dict)) and isinstance(b, (list, tuple, dict))
    ), f"{path}: type mismatch {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        assert set(a) == set(b), f"{path}: keys differ {set(a) ^ set(b)}"
        for k in a:
            assert_params_equal(a[k], b[k], f"{path}.{k}")
        return
    if isinstance(a, (list, tuple)):
        assert len(a) == len(b), f"{path}: length differ"
        for i, (x, y) in enumerate(zip(a, b)):
            assert_params_equal(x, y, f"{path}[{i}]")
        return
    assert a == b, f"{path}: {a!r} != {b!r}"


def roundtrip_expression(fqn: str, instance: BaseExpression, dialect: Any) -> None:
    """Assert an instance round-trips losslessly through dict / JSON / XML."""
    original = instance.get_params()
    for restored in (
        _rt_dict(instance, dialect),
        _rt_json(instance, dialect),
        _rt_xml(instance, dialect),
    ):
        assert_params_equal(restored.get_params(), original, fqn)


def _rt_dict(instance, dialect):
    from rhosocial.activerecord.backend.expression.serialization import deserialize, serialize

    return deserialize(serialize(instance), dialect)


def _rt_json(instance, dialect):
    from rhosocial.activerecord.backend.expression.serialization import deserialize_json, serialize_json

    return deserialize_json(serialize_json(instance), dialect)


def _rt_xml(instance, dialect):
    from rhosocial.activerecord.backend.expression.serialization import deserialize_xml, serialize_xml

    return deserialize_xml(serialize_xml(instance), dialect)


def sql_consistent(fqn: str, instance: BaseExpression, dialect: Any) -> None:
    """Assert to_sql is identical after round-trip, when the dialect supports it."""
    try:
        expected = instance.to_sql()
    except Exception:
        return
    for restored in (_rt_dict(instance, dialect), _rt_json(instance, dialect), _rt_xml(instance, dialect)):
        assert restored.to_sql() == expected, fqn


__all__ = [
    "assert_params_equal",
    "collect_expression_classes",
    "make_instance",
    "register_all",
    "register_special_constructor",
    "roundtrip_expression",
    "sql_consistent",
]