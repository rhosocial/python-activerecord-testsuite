# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_protocol_guarantees.py
"""The guarantees the column-type protocol claims, asserted per backend.

``test_typed_column_contracts.py`` answers *what a column class means*: that an
explicit declaration is backend-independent, and that inference follows the
backend's own tables. This file answers a different question — whether the
protocol's own claims hold — and the four are:

1. **Completeness** — every backend answers every common entry. A hole is a
   failure, not a skip: a backend that forgets an entry would otherwise pass
   its own suite and fail only on whichever model happened to use the
   forgotten type, a failure whose site and whose cause are far apart.
2. **Answer states** — each answer is a column class, or ``None`` for "this
   backend genuinely has no workaround here". Anything else — a string,
   another type — is a malformed table and is read as a column class by
   whichever consumer meets it first.
3. **Orthogonality** — a field's DDL type cannot reach its expressions,
   because the column object has no slot for it and carries no value-family
   label at all.
4. **No universal column** — an annotation the vocabulary does not cover
   fails, naming the way out; it does not silently degrade to a permissive
   column.

Why these are contracts and not unit tests
------------------------------------------
Each one can be violated by a backend that still passes every test in its own
repository, and the symptom would be a model behaving differently on one server
than on the rest — the exact failure the typed-column work exists to remove. So
they run against every backend, through the provider's configured dialect.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_protocol_guarantees.py
import inspect
from typing import Any, Optional, Union

import pytest

from rhosocial.activerecord.backend.expression import (
    Column,
    ColumnBase,
)
from rhosocial.activerecord.base.field_proxy import ColumnTypeResolutionError
from rhosocial.activerecord.base.fields import UseColumnType

from rhosocial.activerecord.testsuite.feature.query.typed_column.column_helpers import (
    COMMON_TYPES,
    resolve_column_class,
)


def _name(entry):
    return getattr(entry, "__name__", str(entry))


# ---------------------------------------------------------------------------
# 1. Completeness: a hole is a failure, not a skip
# ---------------------------------------------------------------------------


def test_every_common_entry_of_the_protocol_is_answered(dialect):
    """Every entry of the shared list gets an answer from this backend.

    The answer may be a real column class or an explicit ``None``: refusing is
    a legitimate, measured conclusion, and the explicit ``None`` exists
    precisely so that "no" and "unconsidered" stay distinguishable. What is not
    allowed is absence, because absence is what an oversight looks like.
    """
    table = dialect.suggested_column_types()
    unanswered = [entry for entry in COMMON_TYPES if entry not in table]

    assert not unanswered, (
        f"{type(dialect).__name__}.suggested_column_types() leaves "
        f"{len(unanswered)} entr{'y' if len(unanswered) == 1 else 'ies'} of the "
        f"common list unanswered: {[_name(e) for e in unanswered]}. Answer "
        f"None rather than omitting, so a refusal stays distinguishable from "
        f"an oversight."
    )


def test_an_omitted_entry_fails_at_selection_rather_than_defaulting():
    """A table with a hole is the backend's omission, and nothing papers over it.

    There is no fallback table and no permissive column: the selection either
    finds the entry in the backend's own table or fails, telling the caller how
    to declare explicitly. Deliberately not parameterised over the backends:
    every backend passes the completeness contract above, so forcing a hole
    requires a dialect built for the purpose.

    The hole is made by removing ``str`` rather than ``bool``. ``bool``
    subclasses ``int``, so dropping it from the table would leave the subclass
    walk to find ``int`` and the omission would be invisible — which is why the
    completeness contract above checks for *key presence* rather than for
    resolvability.
    """
    table = {entry: Column for entry in COMMON_TYPES}
    table.pop(str)

    class _WithHole:
        NAME = "with_hole"

        def suggested_column_types(self):
            return dict(table)

        def suggested_extra_column_types(self):
            return {}

    with pytest.raises(ColumnTypeResolutionError) as err:
        resolve_column_class(_WithHole(), str)

    message = str(err.value)
    assert "UseColumnType" in message, (
        f"An omitted entry must leave the caller a route forward. Got: {message!r}"
    )


# ---------------------------------------------------------------------------
# 2. The table has exactly two answer states
# ---------------------------------------------------------------------------


def test_the_answer_for_each_entry_is_a_class_or_none(dialect):
    """No third state: a column class, or an explicit ``None``.

    ``None`` is the deliberate "this backend genuinely has no column for this
    value, and no workaround expresses it" — the last resort, not a first
    answer. A table entry that is anything else is read as a column class by
    whichever consumer meets it first and would fail much later, in SQL this
    contract cannot see. Checking the *table* makes a malformed cell the
    backend's own test failure rather than a surprise at the first query.
    """
    table = dialect.suggested_column_types()
    malformed = [
        (_name(entry), value)
        for entry, value in table.items()
        if value is not None
        and not (isinstance(value, type) and issubclass(value, ColumnBase))
    ]

    assert not malformed, (
        f"{type(dialect).__name__} answers with something that is neither a "
        f"column class nor None: {malformed}. The two states are a class and "
        f"the explicit None; absence is reserved for entries the protocol does "
        f"not carry."
    )


def test_every_answered_class_is_constructible(dialect):
    """A class in the table is only real if a column can be built from it.

    The table answering correctly and the class refusing to construct would
    leave the failure at query time with a message about a column rather than
    about the annotation, which is the outcome the narrow column classes were
    introduced to remove.
    """
    for entry, value in dialect.suggested_column_types().items():
        if value is None:
            continue
        column = value(dialect, "c")
        assert isinstance(column, ColumnBase), (
            f"{type(dialect).__name__} answers {value!r} for {_name(entry)}, "
            f"which does not build a column"
        )


# ---------------------------------------------------------------------------
# 3. Orthogonality: the DDL type cannot reach the expression
# ---------------------------------------------------------------------------


def test_the_column_object_has_no_slot_for_a_fields_data_type(dialect):
    """The mechanical form of the orthogonality ruling.

    The column object carries ``(name, column class)`` and its constructor
    offers no place to put a field's DataType or a value-family label, so
    making an expression depend on one would first require changing the object
    model — which is reviewable, unlike a value quietly read out of field
    metadata at render time.
    """
    parameters = [
        name
        for name in inspect.signature(Column.__init__).parameters
        if name != "self"
    ]

    leaked = [
        name
        for name in parameters
        if any(
            word in name.lower()
            for word in ("data_type", "sql_type", "datatype", "value_type")
        )
    ]

    assert not leaked, (
        f"Column.__init__ gained a slot a field's DataType or value-family "
        f"label could travel through: {leaked}. Orthogonality is enforced by "
        f"there being nowhere to put it; adding the parameter is the change "
        f"that breaks it, and it must be reviewed as such rather than absorbed."
    )


def test_no_value_family_label_remains(dialect):
    """The label was removed outright: the column class *is* the value type.

    A string naming the annotation's family used to ride on the column; it was
    a tag that could only ever drift from the class, and the class already says
    what the value can do. Asserting its absence keeps a future re-introduction
    a reviewed change rather than a quiet readdition.
    """
    any_class = next(
        value
        for value in dialect.suggested_column_types().values()
        if isinstance(value, type) and issubclass(value, ColumnBase)
    )
    assert not hasattr(any_class(dialect, "c"), "value_type")


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
    is a failure that names the escape hatch, so the caller either annotates
    with a type the protocol carries or declares the operations explicitly.

    The message is part of the contract: a bare "could not resolve" leaves the
    reader guessing which of the two routes to take.
    """
    with pytest.raises(ColumnTypeResolutionError) as err:
        resolve_column_class(dialect, annotation)

    message = str(err.value)
    assert "UseColumnType" in message, (
        f"The failure must name the escape hatch. Got: {message!r}"
    )


def test_the_escape_hatch_reaches_past_a_none_answer(dialect):
    """Declaring wins before the tables are consulted.

    The whole point of the declaration is that it is the *only* route past a
    refusal, so it has to be consulted before the table — otherwise a backend
    with an explicit ``None`` for an annotation would be unreachable for that
    field even though its value supports operations the backend can render.
    Firebird's JSON answer is the recorded case that keeps this honest.
    """

    class _RefusingDict:
        NAME = "refusing_dict"

        def suggested_column_types(self):
            table = dict(dialect.suggested_column_types())
            table[dict] = None
            return table

        def suggested_extra_column_types(self):
            return dialect.suggested_extra_column_types()

    with pytest.raises(ColumnTypeResolutionError):
        resolve_column_class(_RefusingDict(), dict)

    declared = UseColumnType(Column)
    assert resolve_column_class(_RefusingDict(), dict, declared) is Column


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
    if not (isinstance(column_class, type) and issubclass(column_class, ColumnBase)):
        pytest.skip(f"{type(dialect).__name__} does not answer a class for str")
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
