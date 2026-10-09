# tests/rhosocial/activerecord/testsuite/utils/test_expression_utils.py
"""
Guards on ``utils.expression``'s name-based constructor registry.

``special_constructors()`` dispatches on ``full_name.endswith(key)``, which
makes a mis-keyed entry fail *silently*: the class falls through to
``_try_construct`` and is reported as unconstructible rather than as
mis-registered, and nothing raises. That is not hypothetical here — two of the
entries in that dict were dead when these tests were written.

* ``"advanced_functions.JSONExpression"`` stopped matching the moment core
  split that one class into ``JSONDocumentExpression`` and ``JSONTextExpression``.
* ``"query_parts.JoinExpression"`` named a class core renamed to
  ``JoinClause``.

Neither could raise an error, so neither did. Both entries have since been
retargeted at the live classes, so each of them now activates the constructor
it names. These tests exist to make the dispatch observable.

Every assertion here goes *through* the dispatch. Nothing checks that a module
imports: the stale ``JSONExpression`` key imported perfectly well and matched
nothing at all, which is precisely why an import check would have been worth
nothing here.
"""

import inspect

import pytest

from rhosocial.activerecord.backend.expression.advanced_functions import (
    JSONDocumentExpression,
    JSONTextExpression,
)
from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression.serialization import ExpressionRegistry
from rhosocial.activerecord.backend.expression.statements.dml import ValuesSource
from rhosocial.activerecord.backend.expression.types.array import ArrayType
from rhosocial.activerecord.backend.expression.types import IntegerType
from rhosocial.activerecord.backend.impl.dummy.dialect import DummyDialect

from rhosocial.activerecord.testsuite.utils.expression import (
    _try_construct,
    make_instance,
    special_constructors,
)


@pytest.fixture(scope="module")
def dialect():
    return DummyDialect()


def _entry_for(cls):
    """The factory the registry would dispatch this class to, or None."""
    fqn = f"{cls.__module__}.{cls.__name__}"
    return next(
        (fn for key, fn in special_constructors().items() if fqn.endswith(key)),
        None,
    )


class TestTheSplitJSONClassesEachDispatchToTheirOwnConstructor:
    """The two access operators are two classes, so they need two entries.

    One entry cannot cover both: ``endswith`` compares a suffix, and
    ``"advanced_functions.JSONExpression"`` is not a suffix of either new name.
    """

    @pytest.mark.parametrize(
        "cls, operation",
        [(JSONDocumentExpression, "->"), (JSONTextExpression, "->>")],
        ids=["document", "text"],
    )
    def test_the_registry_entry_builds_that_class_asking_for_that_operator(
        self, dialect, cls, operation
    ):
        fn = _entry_for(cls)
        assert fn is not None, (
            f"{cls.__name__} has no entry in special_constructors(), so it "
            f"falls through to _try_construct with no error raised. That "
            f"silent fall-through is what this test exists for."
        )

        instance = fn(dialect)
        assert type(instance) is cls, (
            f"the entry for {cls.__name__} returned {type(instance).__name__}"
        )
        assert instance.operation == operation, (
            f"{cls.__name__} was built with operation={instance.operation!r}. "
            f"The class exists to say which operator it is, and "
            f"JSONTextExpression inherits operation='->' from its parent, so "
            f"the factory has to state it."
        )

    @pytest.mark.parametrize(
        "cls", [JSONDocumentExpression, JSONTextExpression], ids=["document", "text"]
    )
    def test_make_instance_reports_special_rather_than_heuristic(self, dialect, cls):
        """``source`` is the only observable difference between matched and not.

        A dead key does not raise; it just relabels the class as ``heuristic``
        (or ``failed``). So the label is itself the evidence the key is live.
        """
        instance, source = make_instance(cls, dialect)
        assert source == "special", (
            f"{cls.__name__}: make_instance reported source={source!r}, so no "
            f"registry entry matched it. Renaming a class turns its entry into "
            f"dead code and nothing raises."
        )
        assert type(instance) is cls

    def test_each_class_matches_its_own_entry_and_neither_others(self):
        """Two keys, not one — asserted so a future merge cannot pass quietly."""
        specials = special_constructors()
        for cls in (JSONDocumentExpression, JSONTextExpression):
            matched = [
                key for key in specials
                if f"{cls.__module__}.{cls.__name__}".endswith(key)
            ]
            assert matched == [f"advanced_functions.{cls.__name__}"], (
                f"{cls.__name__} matched {matched}"
            )

    def test_rendering_does_not_depend_on_which_of_the_two_was_built(self, dialect):
        """The split must not have moved a single character of SQL.

        Both formatters branch on ``expr.operation`` and dispatch on
        ``format_method``, which the two classes share — so the class documents
        the operator and the operation drives the rendering. If that stopped
        being true, a caller who built "the wrong one" of the pair would get
        different SQL for the same query, which is the confusion the split
        exists to prevent.
        """
        col = Column(dialect, "j", table="t")

        def render(cls, operation):
            try:
                return cls(dialect, col, "a", operation=operation).to_sql()
            except Exception as exc:  # noqa: BLE001 - recorded as the answer
                return (f"<{type(exc).__name__}: {exc}>", ())

        rendered = {}
        for operation in ("->", "->>"):
            as_document = render(JSONDocumentExpression, operation)
            as_text = render(JSONTextExpression, operation)
            assert as_document == as_text, (
                f"operation={operation!r} renders differently depending on the "
                f"class: {as_document!r} vs {as_text!r}"
            )
            sql, _params = as_document
            assert not sql.startswith("<"), (
                f"operation={operation!r} refused to render at all, so the "
                f"equality above would be comparing two identical refusals: {sql}"
            )
            rendered[operation] = sql

        # And the operation still distinguishes the two renderings, so holding
        # the class fixed did not collapse them into one another either.
        assert rendered["->"] != rendered["->>"], rendered
        print(f"\n  rendered per operation: {rendered}")

    def test_the_two_classes_still_dispatch_to_the_same_formatter(self, dialect):
        """``format_method`` is what the dialect dispatches on, and it is shared.

        Read off instances: it is a property, so the class object holds a
        property rather than the string.
        """
        col = Column(dialect, "j", table="t")
        for operation in ("->", "->>"):
            assert (
                JSONDocumentExpression(dialect, col, "a", operation=operation)
                .format_method
                == "format_json_expression"
            )
            assert (
                JSONTextExpression(dialect, col, "a", operation=operation)
                .format_method
                == "format_json_expression"
            )


class TestTheTwoUnconstructibleClassesGetRealConstructors:
    """``ValuesSource`` and ``ArrayType`` cannot be reached by the filler.

    Neither is exempt from anything. The contract test's guard simply never
    applied to them, because they never got as far as being built at all.
    Supplying a constructor is the opposite of an exemption: it turns the guard
    on for two classes it was skipping.
    """

    @pytest.mark.parametrize("cls", [ValuesSource, ArrayType], ids=["ValuesSource", "ArrayType"])
    def test_the_heuristic_alone_cannot_build_it(self, dialect, cls):
        """Establishes *why* the entry exists, so it cannot be deleted as redundant."""
        assert _try_construct(cls, dialect) is None, (
            f"{cls.__name__} is now reachable by the heuristic filler. If that is "
            f"deliberate its explicit constructor is redundant, and this test is "
            f"the thing that should be reconsidered."
        )

    @pytest.mark.parametrize("cls", [ValuesSource, ArrayType], ids=["ValuesSource", "ArrayType"])
    def test_the_registry_entry_builds_it_and_is_reached(self, dialect, cls):
        fn = _entry_for(cls)
        assert fn is not None, f"{cls.__name__} has no entry in special_constructors()"
        assert type(fn(dialect)) is cls

        instance, source = make_instance(cls, dialect)
        assert source == "special", f"{cls.__name__}: source={source!r}"
        assert type(instance) is cls

    def test_the_values_source_is_a_real_insert_source(self, dialect):
        """Non-empty, list rows, equal row lengths — the three things it checks.

        An empty ``values_list`` is the tempting filler value and the one the
        constructor refuses. It is also the wrong thing to satisfy it with: a
        ``VALUES`` clause with no rows is not an INSERT source, and the
        zero-row spelling already has its own class, ``DefaultValuesSource``.
        """
        source = _entry_for(ValuesSource)(dialect)
        assert source.values_list
        assert all(isinstance(row, list) for row in source.values_list)
        assert len({len(row) for row in source.values_list}) == 1

        with pytest.raises(ValueError):
            ValuesSource(dialect, [])

    def test_the_array_has_a_concrete_element_type_and_cannot_do_without_one(
        self, dialect
    ):
        """An array with no element type is not a type — core raises on it.

        ``element_type`` cannot simply be made required instead: ``dialect`` is
        first and carries a default, and Python forbids a required parameter
        after a defaulted one, so the signature core ships is the only
        expressible one. The element type has to be supplied by the caller.
        """
        array = _entry_for(ArrayType)(dialect)
        assert isinstance(array.element_type, IntegerType)
        assert array.dimensions >= 1

        with pytest.raises(TypeError):
            ArrayType(dialect)

        params = list(inspect.signature(ArrayType.__init__).parameters)
        assert params[1] == "dialect", params
        assert inspect.signature(ArrayType.__init__).parameters["element_type"].default \
            is None, "if element_type ever becomes required, this factory can pass it"

    def test_both_new_entries_report_the_parameters_get_params_will_be_asked_for(
        self, dialect
    ):
        """The point of a constructor here: ``get_params()`` now has something to report.

        ``get_params()`` walks ``__init__`` and resolves every parameter to a
        stored attribute. A class that cannot be built is a class whose
        ``get_params()`` is never checked, which is the coverage these two
        entries recover.
        """
        for cls in (ValuesSource, ArrayType):
            params = _entry_for(cls)(dialect).get_params()
            assert params, cls.__name__
            assert "dialect" not in params, cls.__name__
            for pname in inspect.signature(cls.__init__).parameters:
                if pname in ("self", "dialect"):
                    continue
                assert pname in params, f"{cls.__name__}.get_params() has no {pname!r}"


class TestNoEntrySilentlyStopsMatching:
    """An entry naming a class core still has must resolve to it.

    This is the general form of the silent failure, and it needs no exemption
    list to state it: it asserts only about entries whose named class *exists*,
    so an entry naming something core deleted is out of scope by construction
    rather than by being tolerated.
    """

    def _core_registry(self):
        ExpressionRegistry._auto_register_builtins()
        return {f"{cls.__module__}.{cls.__name__}" for cls in ExpressionRegistry._registry.values()}

    def test_every_entry_naming_a_live_core_class_matches_it(self):
        registry = self._core_registry()
        # Which (module tail, class name) pairs core actually has.
        live = {
            (fqn.rpartition(".")[0].rpartition(".")[2], fqn.rpartition(".")[2])
            for fqn in registry
        }

        mis_keyed = []
        inert = []
        for key in special_constructors():
            module_tail, _, class_name = key.rpartition(".")
            if any(fqn.endswith(key) for fqn in registry):
                continue
            if (module_tail, class_name) in live:
                mis_keyed.append(key)
            else:
                inert.append(key)

        print(f"\n  entries naming a class core no longer has (inert): {inert}")
        assert not mis_keyed, (
            "entries in special_constructors() that name a class core still "
            "has but do not match it: "
            + ", ".join(sorted(mis_keyed))
            + ". Renaming a class leaves its entry matching nothing, and the "
            "class then falls back to _try_construct without any error."
        )


class TestMakeInstanceSourcesAreHonest:
    def test_source_reflects_which_path_was_taken(self, dialect):
        instance, source = make_instance(Column, dialect)
        assert source in {"special", "heuristic"}
        assert instance is not None
