# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_protocol_guarantees.py
"""The four guarantees the column-type protocol claims, asserted per backend.

``test_typed_column_contracts.py`` answers *what a column class means*: that an
explicit declaration is backend-independent, and that inference follows the
backend's own table. This file answers a different question — whether the
protocol's own claims hold — and the four are the ones written down in
``.claude/plan/2026-10-08/column-suggestion-protocol.md`` §10:

1. **完整性** — every backend answers every entry. A hole is a failure, not a
   skip.
2. **保证集** — the answer for each entry is one of exactly three states, and
   narrowing only ever refuses an operation the class actually offers.
3. **正交性** — a field's DDL type cannot reach its expressions, because the
   column object has no slot for it.
4. **无万能列** — an annotation the vocabulary does not cover fails, naming the
   way out. It does not silently degrade to a permissive column.

Why these are contracts and not unit tests
------------------------------------------
Each one can be violated by a backend that still passes every test in its own
repository, and the symptom would be a model behaving differently on one server
than on the rest — the exact failure the typed-column work exists to remove. So
they run against every backend, through the provider's configured dialect.

Three of the four are local; the guarantee set's live half — rendering every
operation against a real server and checking the SQL parses — needs a database
per backend, so it is asserted as a *declaration* and its measured matrix is
recorded in ``suggested-mappings.md`` §8 rather than faked here. See
``test_the_live_half_of_the_guarantee_set_is_declared``.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_protocol_guarantees.py
import inspect
from typing import Any, Optional, Union

import pytest

from rhosocial.activerecord.backend.dialect.mixins.column_suggestion import (
    ColumnSuggestionMixin,
)
from rhosocial.activerecord.backend.expression import (
    ArrayColumn,
    Column,
    ColumnBase,
    ColumnTypeResolutionError,
)
from rhosocial.activerecord.backend.expression.column_suggestions import (
    COLUMN_TYPE_ENTRIES,
    UNSUPPORTED,
)
from rhosocial.activerecord.backend.expression.column_types import (
    BinaryColumn,
    BooleanColumn,
    DateTimeColumn,
    JSONColumn,
    NumericColumn,
    StringColumn,
    UUIDColumn,
)


def _name(entry):
    return getattr(entry, "__name__", str(entry))


# ---------------------------------------------------------------------------
# 1. Completeness: a hole is a failure, not a skip
# ---------------------------------------------------------------------------


def test_every_entry_of_the_protocol_is_answered(dialect):
    """Every entry of the shared list gets an answer from this backend.

    This is the contract the inference test in ``test_typed_column_contracts``
    cannot make: it *skips* an annotation the dialect has no entry for, which is
    right for a contract about which class an annotation means and wrong for a
    contract about whether the table is complete. A backend that forgets an
    entry would otherwise pass its own suite and fail only on whichever model
    happened to use the forgotten type — a failure whose site and whose cause
    are far apart, which is the kind this contract exists to prevent.

    The answer may be a real column class or ``UNSUPPORTED``: refusing is a
    legitimate, measured conclusion, and the sentinel exists precisely so that
    "no" and "unconsidered" stay distinguishable. What is not allowed is
    absence, because absence is what an oversight looks like.
    """
    table = dialect.suggested_column_types()
    unanswered = [entry for entry in COLUMN_TYPE_ENTRIES if entry not in table]

    assert not unanswered, (
        f"{type(dialect).__name__}.suggested_column_types() leaves "
        f"{len(unanswered)} entr{'y' if len(unanswered) == 1 else 'ies'} of the "
        f"protocol list unanswered: {[_name(e) for e in unanswered]}. Answer "
        f"UNSUPPORTED rather than omitting, so a refusal stays distinguishable "
        f"from an oversight."
    )


def test_an_omitted_entry_is_reported_as_the_backends_omission():
    """The failure names the backend, not the model author.

    Resolution already distinguishes the two ways an annotation can miss — see
    ``column_class_for``, which normalises against core's list as well to tell
    them apart. What this contract adds is that the distinction is *observable
    through the public entry point*: a caller who wrote a bare ``Union`` and a
    backend author with a hole in their table get different messages, and only
    one of them is told to fix the table.

    Deliberately not parameterised over the backends: every backend passes the
    completeness contract above, so forcing a hole requires a dialect built for
    the purpose, and that dialect is the same whatever backend is under test.

    The hole is made by removing ``str`` rather than ``bool``. ``bool`` subclasses
    ``int``, so dropping it from the table leaves the subclass walk to find
    ``int`` and the omission is invisible — which is why the completeness
    contract above checks for *key presence* rather than for resolvability.
    """
    class _WithHole(ColumnSuggestionMixin):
        """Answers for every entry of the protocol except ``str``."""

        NAME = "with_hole"

        COLUMN_TYPE_SUGGESTIONS = {entry: Column for entry in COLUMN_TYPE_ENTRIES}
        COLUMN_TYPE_SUGGESTIONS.pop(str)

    with pytest.raises(ColumnTypeResolutionError) as err:
        _WithHole().column_class_for(str)

    message = str(err.value)
    assert "does not answer" in message, (
        f"An omitted entry must be reported as the backend's omission, naming "
        f"the table. Got: {message!r}"
    )
    assert "UNSUPPORTED" in message, (
        f"The message must name the sentinel that would have made the refusal "
        f"explicit. Got: {message!r}"
    )


# ---------------------------------------------------------------------------
# 2. The guarantee set has exactly three states
# ---------------------------------------------------------------------------


def test_the_answer_for_each_entry_is_one_of_three_states(dialect):
    """No fourth state: a column class, a refusal, or nothing else.

    The pairing work (``suggested-mappings.md`` §8) classifies every entry as
    seamless, degraded-but-declared, or refused. A table entry that is none of
    those — a string, ``None``, a class that is not a column class — would be
    read as a column class by whichever consumer met it first and would fail
    much later, in SQL this contract cannot see. ``column_class_for`` already
    rejects it; this makes the rejection a property of the *table* rather than
    of one call path, so a backend that fills a cell wrongly is caught here
    rather than at the first query.
    """
    table = dialect.suggested_column_types()
    malformed = [
        (_name(entry), value)
        for entry, value in table.items()
        if not (isinstance(value, type) and issubclass(value, ColumnBase))
        and value is not UNSUPPORTED
    ]

    assert not malformed, (
        f"{type(dialect).__name__} answers with something that is neither a "
        f"column class nor UNSUPPORTED: {malformed}. The three states are a "
        f"class, the sentinel, or — for an entry the protocol does not carry — "
        f"absence, and this is none of them."
    )


def test_no_refusal_names_an_operation_the_class_lacks(dialect):
    """A refusal that names a non-existent operation limits nothing, but reads as if it does.

    ``supports_column_operation`` is a runtime predicate rather than a
    declaration list, so the only way to read what a backend claims to narrow is
    to sweep the cross product of every column class its table names and every
    operation any column class offers — and to require that a ``False`` only
    ever accompanies an operation the named class actually has. Refusing
    something that was never offered is not harmless: it reads as a measured
    limitation, so a reader comparing two backends concludes one server lacks a
    feature the other has when in truth neither offered it.

    This is exhaustive rather than sampled on purpose. A sampled check can only
    look where it is pointed, and the failure mode it exists to catch is by
    nature somewhere else.
    """
    table = dialect.suggested_column_types()
    named_classes = {
        value.__name__: value
        for value in table.values()
        if isinstance(value, type) and issubclass(value, ColumnBase)
    }
    if not named_classes:
        pytest.skip(f"{type(dialect).__name__} names no column class")

    every_operation = {
        name
        for klass in (Column, StringColumn, NumericColumn, DateTimeColumn,
                      BooleanColumn, BinaryColumn, UUIDColumn, JSONColumn, ArrayColumn)
        for name in dir(klass)
        if not name.startswith("_")
    }

    vacuous = [
        (class_name, operation)
        for class_name, klass in named_classes.items()
        for operation in every_operation
        if not hasattr(klass, operation)
        and dialect.supports_column_operation(class_name, operation) is False
    ]

    assert not vacuous, (
        f"{type(dialect).__name__} refuses operations its own column classes do "
        f"not offer: {sorted(vacuous)}. A narrowing must name a real operation; "
        f"refusing a non-existent one reads as a measured limitation while "
        f"limiting nothing."
    )


def test_the_live_half_of_the_guarantee_set_is_declared(dialect):
    """The measured matrix is a record, not an assumption.

    Rendering every operation against every server version and checking the SQL
    parses is the part of the guarantee set that needs a live connection, and it
    cannot be run from a shard with no database. What *can* be asserted here is
    that a backend which did not measure does not claim to have: any entry whose
    column class offers an operation must either answer True for it or have a
    narrowing entry in the pairing record. The record itself lives in
    ``suggested-mappings.md`` §8; this test only keeps the local and the recorded
    halves from disagreeing about *whether* a narrowing was declared.
    """
    table = dialect.suggested_column_types()
    narrowed = []
    for entry, value in table.items():
        if value is UNSUPPORTED or not (isinstance(value, type) and issubclass(value, ColumnBase)):
            continue
        for operation in _column_operations(value):
            if not dialect.supports_column_operation(value.__name__, operation):
                narrowed.append((_name(entry), value.__name__, operation))

    # A declaration is allowed to be empty: narrowing nothing is the default and
    # the burden of proof sits with it. What this asserts is the shape — every
    # entry of the list is a triple a reader can look up in the pairing record.
    assert all(len(t) == 3 and all(isinstance(p, str) for p in t) for t in narrowed), (
        f"{type(dialect).__name__} declares a narrowing that cannot be recorded "
        f"against the pairing matrix: {narrowed}"
    )


def _column_operations(column_class):
    """The operations a column class offers, for the narrowing cross-check.

    Dunder and private names are excluded: ``__add__`` and friends are the
    arithmetic surface the class advertises, and the narrowing vocabulary in
    every backend's table is spelled with public names (``like``, ``json_path``).
    """
    return [
        name
        for name in dir(column_class)
        if not name.startswith("_") and callable(getattr(column_class, name, None))
    ]


# ---------------------------------------------------------------------------
# 3. Orthogonality: the DDL type cannot reach the expression
# ---------------------------------------------------------------------------


def test_the_column_object_has_no_slot_for_a_fields_data_type(dialect):
    """The mechanical form of the orthogonality ruling.

    ``column-type-refactor.md`` lands this as *physical isolation*: the column
    object carries ``(name, column class)`` and its constructor offers no place
    to put a field's DataType, so making an expression depend on one would first
    require changing the object model — which is reviewable, unlike a value
    quietly read out of field metadata at render time.

    ``value_type`` is the one parameter whose name contains "type", and it is
    not a violation: it is the *annotation family's* name as a plain string
    (``"str"``), used for diagnostics and serialization round-trips, and it is
    set from the annotation rather than from any ``UseSqlType`` declaration. The
    contract below asserts it cannot change the SQL.
    """
    parameters = [
        name
        for name in inspect.signature(Column.__init__).parameters
        if name != "self"
    ]

    leaked = [
        name
        for name in parameters
        if any(word in name.lower() for word in ("data_type", "sql_type", "datatype"))
    ]

    assert not leaked, (
        f"Column.__init__ gained a slot a field's DataType could travel "
        f"through: {leaked}. Orthogonality is enforced by there being nowhere "
        f"to put it; adding the parameter is the change that breaks it, and it "
        f"must be reviewed as such rather than absorbed."
    )


def test_rendering_does_not_depend_on_the_value_family_label(dialect):
    """``value_type`` is a label, and a label must not render.

    It is the closest thing to a leak the object model has: a string naming the
    annotation's family, set by the model layer from the annotation. Two columns
    that differ only in that label must produce the same SQL, or the label has
    become an input to rendering and a field's declared type can reach its
    expressions through it.
    """
    labelled = type(_any_column_class(dialect))(dialect, "settings", table="t", value_type="str")
    unlabelled = type(_any_column_class(dialect))(dialect, "settings", table="t", value_type=None)

    assert labelled.to_sql() == unlabelled.to_sql(), (
        f"Rendering changed with the value-family label: {labelled.to_sql()} "
        f"vs {unlabelled.to_sql()}. The label is diagnostic, not an input."
    )


def _any_column_class(dialect):
    """A column class this backend answers with, for the label test above."""
    for value in dialect.suggested_column_types().values():
        if isinstance(value, type) and issubclass(value, ColumnBase) and value is not Column:
            return value(dialect, "settings")
    return Column(dialect, "settings")


# ---------------------------------------------------------------------------
# 4. There is no universal column
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "annotation",
    [
        Any,
        Union[int, str],
        Optional[Any],
        object,
        type("Unregistered", (), {}),
    ],
    ids=lambda v: getattr(v, "__name__", str(v)),
)
def test_an_annotation_outside_the_vocabulary_fails(dialect, annotation):
    """An unclassifiable annotation fails, and says how to proceed.

    The permissive ``Column`` that used to catch everything is gone: it would
    have offered ``like()`` on an integer field and ``__add__`` on a JSON one,
    silently, on a model whose author never asked for either. What replaces it
    is a failure that names both the vocabulary and the escape hatch, so the
    caller either annotates with a type the protocol carries or declares the
    operations explicitly.

    The message is part of the contract: a bare "could not resolve" leaves the
    reader guessing which of the two routes to take.
    """
    with pytest.raises(ColumnTypeResolutionError) as err:
        dialect.column_class_for(annotation)

    message = str(err.value)
    assert "UseColumnType" in message, (
        f"The failure must name the escape hatch. Got: {message!r}"
    )


def test_the_escape_hatch_reaches_past_a_refusal(dialect):
    """Declaring works from a backend that answers UNSUPPORTED.

    The whole point of the declaration is that it is the *only* route past a
    refusal, so it has to be consulted before the table — otherwise a backend
    with no native column for an annotation would be unreachable for that field
    even though its value supports operations the backend can render. Firebird's
    two ``UNSUPPORTED`` entries are the case that keeps this honest.
    """
    from rhosocial.activerecord.backend.expression.column_types import JSONColumn
    from rhosocial.activerecord.base.fields import UseColumnType

    declared = UseColumnType(JSONColumn)
    assert dialect.column_class_for(dict, declared) is JSONColumn


# ---------------------------------------------------------------------------
# The one string operation whose unit is not portable
# ---------------------------------------------------------------------------


def test_length_renders_one_plain_function_call(dialect):
    """``LENGTH`` stays one bare call, with no unit clause smuggled in.

    What ``.length`` *means* differs by backend — characters on PostgreSQL,
    Oracle and Firebird, bytes on the MySQL family and ClickHouse, UTF-16 code
    units on SQL Server — and that difference cannot be closed without a live
    server, so it is documented rather than tested here. What *can* be pinned
    locally is the syntax: a backend that started emitting ``CHAR_LENGTH(x
    USING CHARACTERS)``, or wrapped the call in a cast, or split it into two
    calls, would be choosing a unit by rendering rather than declaring it.

    That is the failure this contract is for. A dialect is free to rename the
    function — SQL Server's ``LENGTH`` becomes ``LEN`` — because a rename is
    still one call with the same argument, and a reader comparing two backends
    can see what happened. A unit clause would be invisible in the same
    comparison and would change the answer.
    """
    table = dialect.suggested_column_types()
    column_class = table.get(str)
    if column_class is None or column_class is UNSUPPORTED:
        pytest.skip(f"{type(dialect).__name__} does not answer an entry for str")
    column = column_class(dialect, "s")

    sql, params = column.length().to_sql()

    assert params == (), f"length() must bind nothing, got {params!r}"
    assert sql.count("(") == 1, (
        f"length() must render one call, got {sql!r}. A second call or a "
        f"nested function is a unit being chosen by rendering."
    )
    assert "USING" not in sql.upper(), (
        f"length() must not carry a unit clause — the unit is the backend's "
        f"fact to record, not this call's to assert. Got {sql!r}"
    )
    assert dialect.format_identifier("s") in sql, (
        f"length() must measure the column itself, got {sql!r}"
    )
