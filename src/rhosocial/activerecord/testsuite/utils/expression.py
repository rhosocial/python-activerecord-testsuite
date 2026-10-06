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

import collections.abc
import dataclasses
import inspect
import re
import typing
import warnings
from typing import Any, Callable, Dict, List, Optional, Type

from rhosocial.activerecord.backend.expression.bases import BaseExpression

# Annotation fragments that mean "this parameter names a relation object".
# Word boundaries matter: ``TableConstraint`` and ``AddTableConstraint`` are
# constraint actions, not relations, and a substring test would hand them a
# Table. ``SchemaObject`` is the base every catalogue object shares, so an
# annotation naming it wants an object too.
_MENTIONS_RELATION = re.compile(
    r"\b(Table|View|MaterializedView|Index|Sequence|Type|Domain|Function|Trigger"
    r"|Schema|Database|RelationObject|SchemaObject|NodeTable|EdgeTable)\b"
)

# An INSERT's data source. It is an expression now, so it needs a real one --
# the generic placeholder cannot invent the rows a VALUES list is made of.
_MENTIONS_INSERT_SOURCE = re.compile(r"\bInsertDataSource\b")


def _empty_container_for(annotation: Any, dialect: Any):
    """Return an empty container for a parameterised alias, else None.

    A parameterised alias like ``List[str]`` or ``Dict[str, BaseExpression]``
    says what the *elements* are, never the container itself, so there is no
    catalogue object to hand back -- only an empty container. Deciding this
    before the relation-name test is what keeps ``typing.List[str]`` from being
    read as a ``Table``: ``typing.get_origin`` on it gives ``list``, but the
    relation test only ever saw the alias' own name, and ``List[str]`` matches
    ``Sequence``/``Table``-family fragments well enough to be mistaken for one.

    Returns ``None`` when ``annotation`` is not a parameterised container, which
    is the caller's signal to keep reading.
    """
    origin = typing.get_origin(annotation)
    if origin is None:
        return None
    if origin in (list, tuple, set, frozenset):
        return []
    if origin is dict:
        return {}
    # ``Sequence[str]`` and friends resolve to the collections.abc ABC rather
    # than to ``list``, so match on the abstract base instead of the concrete
    # one the annotation happens to name.
    if isinstance(origin, type) and issubclass(origin, (collections.abc.Sequence, collections.abc.Set)):
        return []
    if isinstance(origin, type) and issubclass(origin, collections.abc.Mapping):
        return {}
    return None


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
        container = _empty_container_for(annotation, dialect)
        if container is not None:
            return container
        if raw in (list, tuple, set):
            return []
        if raw is dict:
            return {}
        if _MENTIONS_RELATION.search(text):
            return _relation(dialect, text)
        if _MENTIONS_INSERT_SOURCE.search(text):
            return _values_source(dialect)
        if raw is str or "str" in text:
            return "x"
        if "DataType" in text or "Type" in text.split(".")[-1:]:
            from rhosocial.activerecord.backend.expression.types import IntegerType

            return IntegerType(dialect)
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
        "statements.ddl_table.ColumnDefinition": _column_definition,
        "statements.dml.ValuesSource": _values_source,
        "statements.ddl_sequence.CreateSequenceExpression": _create_sequence_expr,
        "statements.ddl_sequence.DropSequenceExpression": _drop_sequence_expr,
        "statements.ddl_sequence.AlterSequenceExpression": _alter_sequence_expr,
        "statements.ddl_type.CreateTypeExpression": _create_type_expr,
        "statements.ddl_type.AlterTypeExpression": _alter_type_expr,
        "statements.ddl_type.DropTypeExpression": _drop_type_expr,
        "statements.ddl_domain.CreateDomainExpression": _create_domain_expr,
        "statements.ddl_domain.AlterDomainExpression": _alter_domain_expr,
        "statements.ddl_domain.DropDomainExpression": _drop_domain_expr,
        "statements.ddl_function.CreateFunctionExpression": _create_function_expr,
        "statements.ddl_function.DropFunctionExpression": _drop_function_expr,
        "statements.ddl_schema.CreateSchemaExpression": _create_schema_expr,
        "statements.ddl_schema.DropSchemaExpression": _drop_schema_expr,
        "statements.ddl_database.CreateDatabaseExpression": _create_database_expr,
        "statements.ddl_database.DropDatabaseExpression": _drop_database_expr,
        "advanced_functions.JSONExpression": _json_expr,
        "query_parts.JoinClause": _join_expr,
        "statements.ddl_partition.PartitionClause": _partition_clause,
        "statements.dml.OnConflictClause": _on_conflict,
        "statements.dml.UpdateExpression": _update_expr,
        "statements.dml.InsertExpression": _insert_expr,
        "statements.dml.DeleteExpression": _delete_expr,
        "statements.ddl_alter.AlterTableExpression": _alter_table_expr,
        "statements.ddl_view.CreateViewExpression": _create_view_expr,
        "graph.GraphVertex": _graph_vertex,
        "graph.GraphEdge": _graph_edge,
        "graph.VertexTable": _node_table,
        "graph.EdgeTable": _edge_table,
        "graph.GraphTableExpression": _graph_table_expr,
        "graph.CreatePropertyGraphExpression": _create_property_graph_expr,
        "graph.DropPropertyGraphExpression": _drop_property_graph_expr,
        "graph.AlterPropertyGraphExpression": _alter_property_graph_expr,
        "datetime.ExtractExpression": _extract_expr,
        "datetime.DatePartExpression": _datepart_expr,
        "datetime.DateTruncExpression": _datetrunc_expr,
        "datetime.IntervalExpression": _interval_expr,
        "datetime.DateTimeDiffExpression": _datetime_diff_expr,
        "datetime.DateTimeSubtractExpression": _datetime_sub_expr,
        "datetime.DateTimeAddExpression": _datetime_add_expr,
    }


def _column_definition(dialect):
    from rhosocial.activerecord.backend.expression.statements import ColumnDefinition
    from rhosocial.activerecord.backend.expression.types import IntegerType

    return ColumnDefinition(dialect, "col", IntegerType(dialect))


def _values_source(dialect):
    """An INSERT's ``VALUES`` source: one row, one literal.

    The generic placeholder cannot build this one -- ``values_list`` must be a
    non-empty list of equal-length rows -- so it gets an explicit constructor.
    """
    from rhosocial.activerecord.backend.expression.core import Literal
    from rhosocial.activerecord.backend.expression.statements.dml import ValuesSource

    return ValuesSource(dialect, [[Literal(dialect, 1)]])


def _json_expr(dialect):
    from rhosocial.activerecord.backend.expression.advanced_functions import JSONExpression
    from rhosocial.activerecord.backend.expression.core import Literal

    return JSONExpression(dialect, Literal(dialect, '{"a": 1}'), path="$.a")


def _sequence(dialect):
    """A sequence, by kind."""
    from rhosocial.activerecord.backend.expression.objects import Sequence

    return Sequence(dialect, "s")


def _create_sequence_expr(dialect):
    from rhosocial.activerecord.backend.expression.statements.ddl_sequence import (
        CreateSequenceExpression,
    )

    return CreateSequenceExpression(dialect, _sequence(dialect))


def _drop_sequence_expr(dialect):
    from rhosocial.activerecord.backend.expression.statements.ddl_sequence import (
        DropSequenceExpression,
    )

    return DropSequenceExpression(dialect, _sequence(dialect))


def _alter_sequence_expr(dialect):
    from rhosocial.activerecord.backend.expression.statements.ddl_sequence import (
        AlterSequenceExpression,
    )

    return AlterSequenceExpression(dialect, _sequence(dialect))


def _create_type_expr(dialect):
    from rhosocial.activerecord.backend.impl.dummy.expression import _DummyTypeDefinition
    from rhosocial.activerecord.backend.expression.objects import Type
    from rhosocial.activerecord.backend.expression.statements.ddl_type import (
        CreateTypeExpression,
    )
    from rhosocial.activerecord.backend.expression.types import IntegerType

    return CreateTypeExpression(
        dialect, Type(dialect, "t"), _DummyTypeDefinition(dialect, IntegerType(dialect))
    )


def _alter_type_expr(dialect):
    from rhosocial.activerecord.backend.impl.dummy.expression import _DummyTypeAlterAction
    from rhosocial.activerecord.backend.expression.objects import Type
    from rhosocial.activerecord.backend.expression.statements.ddl_type import (
        AlterTypeExpression,
    )

    return AlterTypeExpression(
        dialect, Type(dialect, "t"), [_DummyTypeAlterAction(dialect, "t2")]
    )


def _drop_type_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Type
    from rhosocial.activerecord.backend.expression.statements.ddl_type import (
        DropTypeExpression,
    )

    return DropTypeExpression(dialect, Type(dialect, "t"))


def _create_domain_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Domain
    from rhosocial.activerecord.backend.expression.statements.ddl_domain import (
        CreateDomainExpression,
    )
    from rhosocial.activerecord.backend.expression.types import IntegerType

    return CreateDomainExpression(dialect, Domain(dialect, "d"), IntegerType(dialect))


def _alter_domain_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Literal
    from rhosocial.activerecord.backend.expression.objects import Domain
    from rhosocial.activerecord.backend.expression.statements.ddl_domain import (
        AlterDomainExpression,
        SetDomainDefaultAction,
    )

    return AlterDomainExpression(
        dialect, Domain(dialect, "d"), [SetDomainDefaultAction(dialect, Literal(dialect, 1))]
    )


def _drop_domain_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Domain
    from rhosocial.activerecord.backend.expression.statements.ddl_domain import (
        DropDomainExpression,
    )

    return DropDomainExpression(dialect, Domain(dialect, "d"))


def _create_function_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Function
    from rhosocial.activerecord.backend.expression.statements.ddl_function import (
        CreateFunctionExpression,
    )

    return CreateFunctionExpression(dialect, Function(dialect, "f"))


def _drop_function_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Function
    from rhosocial.activerecord.backend.expression.statements.ddl_function import (
        DropFunctionExpression,
    )

    return DropFunctionExpression(dialect, Function(dialect, "f"))


def _create_schema_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Schema
    from rhosocial.activerecord.backend.expression.statements.ddl_schema import (
        CreateSchemaExpression,
    )

    return CreateSchemaExpression(dialect, Schema(dialect, "s"))


def _drop_schema_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Schema
    from rhosocial.activerecord.backend.expression.statements.ddl_schema import (
        DropSchemaExpression,
    )

    return DropSchemaExpression(dialect, Schema(dialect, "s"))


def _create_database_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Database
    from rhosocial.activerecord.backend.expression.statements.ddl_database import (
        CreateDatabaseExpression,
    )

    return CreateDatabaseExpression(dialect, Database(dialect, "d"))


def _drop_database_expr(dialect):
    from rhosocial.activerecord.backend.expression.objects import Database
    from rhosocial.activerecord.backend.expression.statements.ddl_database import (
        DropDatabaseExpression,
    )

    return DropDatabaseExpression(dialect, Database(dialect, "d"))


def _node_table(dialect):
    """A graph vertex table."""
    from rhosocial.activerecord.backend.expression.graph import VertexTable
    from rhosocial.activerecord.backend.expression.objects import NodeTable

    return VertexTable(dialect, NodeTable(dialect, "n"))


def _edge_table(dialect):
    """A graph edge table declaration."""
    from rhosocial.activerecord.backend.expression.graph import EdgeTable
    from rhosocial.activerecord.backend.expression.objects import (
        EdgeTable as EdgeTableObject,
    )

    return EdgeTable(dialect, EdgeTableObject(dialect, "e"), ["s"], ["d"])


def _graph_vertex(dialect):
    from rhosocial.activerecord.backend.expression.graph import GraphVertex
    from rhosocial.activerecord.backend.expression.objects import NodeTable

    return GraphVertex(dialect, "v", NodeTable(dialect, "n"))


def _graph_edge(dialect):
    from rhosocial.activerecord.backend.expression.graph import (
        GraphEdge,
        GraphEdgeDirection,
    )
    from rhosocial.activerecord.backend.expression.objects import (
        EdgeTable as EdgeTableObject,
    )

    return GraphEdge(dialect, "e", EdgeTableObject(dialect, "e"),
                     GraphEdgeDirection.RIGHT)


def _graph_table_expr(dialect):
    from rhosocial.activerecord.backend.expression.graph import (
        ColumnsClause,
        GraphColumn,
        GraphTableExpression,
        MatchClause,
    )
    from rhosocial.activerecord.backend.expression.objects import PropertyGraph

    return GraphTableExpression(
        dialect,
        PropertyGraph(dialect, "g"),
        MatchClause(
            dialect,
            _graph_vertex(dialect),
            _graph_edge(dialect),
            _graph_vertex(dialect),
        ),
        ColumnsClause(dialect, GraphColumn("v", "name")),
    )


def _create_property_graph_expr(dialect):
    from rhosocial.activerecord.backend.expression.graph import (
        CreatePropertyGraphExpression,
    )
    from rhosocial.activerecord.backend.expression.objects import PropertyGraph

    return CreatePropertyGraphExpression(
        dialect, PropertyGraph(dialect, "g"), [_node_table(dialect)]
    )


def _drop_property_graph_expr(dialect):
    from rhosocial.activerecord.backend.expression.graph import (
        DropPropertyGraphExpression,
    )
    from rhosocial.activerecord.backend.expression.objects import PropertyGraph

    return DropPropertyGraphExpression(dialect, PropertyGraph(dialect, "g"))


def _alter_property_graph_expr(dialect):
    from rhosocial.activerecord.backend.expression.graph import (
        AlterPropertyGraphExpression,
    )
    from rhosocial.activerecord.backend.expression.objects import PropertyGraph

    return AlterPropertyGraphExpression(
        dialect,
        PropertyGraph(dialect, "g"),
        "ADD",
        "VERTEX TABLES",
        vertex_tables=[_node_table(dialect)],
    )


def _table(dialect, name="t"):
    """The catalogue object a statement acts on."""
    from rhosocial.activerecord.backend.expression.objects import Table

    return Table(dialect, name)


def _relation(dialect, annotation):
    """The object an annotation asks for, chosen by the kind it names.

    The kind is not decoration: CREATE VIEW will not accept a Table, and DROP
    MATERIALIZED VIEW will not accept a View. Longest name first, because
    ``MaterializedView`` contains ``View`` and the more specific kind is the one
    an annotation naming it means.
    """
    import rhosocial.activerecord.backend.expression.objects as objects

    for kind in ("MaterializedView", "ForeignTable", "NodeTable", "EdgeTable",
                 "Sequence", "Index", "View", "Table", "Type", "Domain",
                 "Function", "Trigger", "Schema", "Database"):
        if re.search(rf"\b{kind}\b", annotation):
            return getattr(objects, kind)(dialect, "t")
    return _table(dialect)


def _source(dialect, name="t"):
    """A row source over the object a statement acts on.

    A statement that *names* a relation takes the object; a statement that
    *reads rows from* one takes a source over it. The two are not
    interchangeable, so they get their own helper rather than one that guesses
    which position it is filling.
    """
    from rhosocial.activerecord.backend.expression.objects import Table
    from rhosocial.activerecord.backend.expression.sources import NamedRelationRef

    return NamedRelationRef(dialect, Table(dialect, name))


def _join_expr(dialect):
    from rhosocial.activerecord.backend.expression.query_parts import JoinClause
    from rhosocial.activerecord.backend.expression.predicates import ComparisonPredicate
    from rhosocial.activerecord.backend.expression.core import Column

    return JoinClause(
        dialect,
        left_table=_source(dialect, "a"),
        right_table=_source(dialect, "b"),
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


def _insert_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Literal
    from rhosocial.activerecord.backend.expression.statements.dml import (
        InsertExpression,
        ValuesSource,
    )

    return InsertExpression(dialect, into=_table(dialect), source=ValuesSource(dialect, [[Literal(dialect, 1)]]))


def _delete_expr(dialect):
    from rhosocial.activerecord.backend.expression.statements.dml import DeleteExpression

    return DeleteExpression(dialect, tables=_table(dialect))


def _update_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Literal
    from rhosocial.activerecord.backend.expression.statements.dml import UpdateExpression

    return UpdateExpression(dialect, table=_table(dialect), assignments={"a": Literal(dialect, 1)})


def _alter_table_expr(dialect):
    from rhosocial.activerecord.backend.expression.statements.ddl_alter import (
        AddColumn,
        AlterTableExpression,
        DropColumn,
    )
    from rhosocial.activerecord.backend.expression.types import IntegerType

    column = _column_definition(dialect)
    return AlterTableExpression(
        dialect,
        table=_table(dialect, "t"),
        actions=[DropColumn(dialect, "a"), AddColumn(dialect, column=column)],
    )


def _create_view_expr(dialect):
    from rhosocial.activerecord.backend.expression.core import Column
    from rhosocial.activerecord.backend.expression.objects import View
    from rhosocial.activerecord.backend.expression.statements.ddl_view import CreateViewExpression
    from rhosocial.activerecord.backend.expression.statements.dql import QueryExpression

    query = QueryExpression(dialect, select=[Column(dialect, "id")], from_=_source(dialect, "t"))
    return CreateViewExpression(dialect, view=View(dialect, "v"), query=query)


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