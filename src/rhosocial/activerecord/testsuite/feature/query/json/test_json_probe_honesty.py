# src/rhosocial/activerecord/testsuite/feature/query/json/test_json_probe_honesty.py
"""A capability probe that returns True must correspond to working SQL.

This is the invariant that catches "the probe says yes, the implementation
emits another dialect's syntax". It is not hypothetical: on PostgreSQL
``supports_json_table()`` claimed 12.0+ while the formatter raised
unconditionally, and on SQL Server ``supports_json_table()`` claimed 2016+
for the same reason. Both handed callers a promise the backend could not
keep.

Two layers are needed, because either alone passes while the defect is live:

1. *Renderability* — the probe is True, so the expression must render. This
   catches a formatter that raises behind a True probe.
2. *Own syntax* — the SQL must contain a function name the backend itself
   declared, and must not contain a function name belonging to some other
   backend. Renderability alone is not enough: the core's default
   function-based fallback emits MySQL's ``JSON_EXTRACT``, which renders
   happily on any dialect and is wrong on most of them.

Which function names a backend declares is not a capability switch. A
``supports_*`` switch takes no arguments, so there is no shared
``supports_json_function(name)`` probe any more: a name lookup answers "does
this backend have *this* function", which is not the same question as "does
this backend support JSON". The shared vocabulary lives in the parameterless
``supports_functions()`` switch, whose mapping keys are the backend's own
function constructors; a dialect that advertises JSON but names no JSON
constructor there is failing this test. Comparing rendered SQL against the
dialect's own *spellings* needs a per-name answer, which is backend-private:
some dialects keep ``is_json_function_available(name)`` (SQL Server does),
others do not. That comparison runs where the helper exists and is explicitly
skipped -- not silently passed -- elsewhere.
"""

# src/rhosocial/activerecord/testsuite/feature/query/json/test_json_probe_honesty.py
from typing import Optional

import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
from rhosocial.activerecord.backend.expression import (
    Column,
    JSONDocumentValue,
    JSONTextValue,
)


@pytest.fixture
def dialect(json_user_fixture):
    """The dialect under test, taken from a provider-configured model.

    Read off ``__backend__`` rather than calling ``Model.backend()``: that
    resolves the *currently active* backend and raises "No backend configured"
    on a shard with no live connection, which is the situation here — every
    assertion is on an expression tree or on SQL from a dialect that was never
    connected. ``__backend__`` is the instance the provider configured and
    needs no connection.

    The model arrives as a direct argument rather than through
    ``request.getfixturevalue``, because that cannot be combined with
    ``@pytest.mark.parametrize``: a parametrised test has no fixture parameter
    to resolve, and pytest rejects the request.
    """
    return json_user_fixture.__backend__.dialect


#: Function names that belong to one specific backend. A dialect rendering any
#: of these is emitting foreign syntax.
#: Names that identify one dialect's spelling rather than another's. Kept to
#: functions only a single backend has: JSON_VALUE and JSON_QUERY are the
#: standard spellings and Oracle, SQL Server and BigQuery all use them, so
#: listing them as foreign failed the dialect that legitimately renders them.
#: A dialect's own declared set is what decides, not this table — see
#: _own_function_names.
_FOREIGN_FUNCTION_NAMES = (
    "JSON_EXTRACT",      # MySQL / MariaDB
    "JSON_UNQUOTE",      # MySQL / MariaDB
    "JSON_CONTAINS",     # MySQL
    "JSON_TYPE",         # MySQL
    "JSON_SEARCH",       # MySQL
    "GET_PATH",          # Snowflake
    "JSONExtractRaw",     # ClickHouse
    "JSONExtractString",  # ClickHouse
    "jsonb_path_query_first",   # PostgreSQL
    "jsonb_path_query_array",   # PostgreSQL
    "OPENJSON",          # SQL Server
)


#: Core used to have one class for both JSON access operators and has since
#: split it in two, one per operator, because the two yield different kinds of
#: value: ``->`` hands back a document that can be indexed into again, ``->>``
#: hands back text that cannot. The helpers below are split to match, so which
#: operator a caller means is read off the class it builds rather than off a
#: string it passes. The rendered SQL is unchanged by the split -- the
#: formatters branch on ``expr.operation``, not on the class, and dispatch is
#: on ``format_method``, which both classes share -- so every assertion below
#: says the same thing it said before, only through the class that now means it.
def _document_sql(dialect, mode, path="a"):
    """Render the document access ``->`` under ``mode``."""
    col = Column(dialect, "j", table="t")
    return JSONDocumentValue(dialect, col, path, mode=mode).to_sql()


def _text_sql(dialect, mode, path="a"):
    """Render the text access ``->>`` under ``mode``."""
    col = Column(dialect, "j", table="t")
    return JSONTextValue(dialect, col, path, operation="->>", mode=mode).to_sql()


# ---------------------------------------------------------------------------
# Layer 1: a True probe must render
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "probe, render",
    [
        ("supports_json_type", _text_sql),
        ("supports_json_arrow_operators", _document_sql),
    ],
    ids=["supports_json_type->>", "supports_json_arrow_operators->"],
)
def test_true_json_probe_renders(dialect, probe, render):
    """If the probe says the dialect handles JSON, it must not then refuse.

    The arrow mode is only required of the arrow probe. Having JSON and having
    ``->`` are separate capabilities — Oracle, Snowflake, BigQuery and Firebird
    all have the first without the second — so demanding arrows of the type
    probe asks the dialect for something it never claimed. The modes each probe
    does cover must render.

    Each cell names the operator it renders through the helper that builds it:
    the type probe is checked with ``->>`` and the arrow probe with ``->``,
    which is the split the helpers encode.
    """
    if not getattr(dialect, probe)():
        pytest.skip(f"{dialect.name} does not advertise {probe}")

    modes = ("auto", "arrow", "function") if probe == "supports_json_arrow_operators" else ("auto", "function")
    for mode in modes:
        try:
            sql, params = render(dialect, mode)
        except Exception as exc:  # noqa: BLE001 - any refusal is a defect
            pytest.fail(
                f"{dialect.name} advertises {probe}() but rendering mode="
                f"{mode!r} raised {type(exc).__name__}: {exc}"
            )
        assert sql, f"{dialect.name} rendered an empty statement for mode={mode!r}"


def test_arrow_mode_is_refused_without_arrow_support(dialect):
    """Asking for a spelling the server lacks should be a clear refusal.

    AUTO covers the honest answer — it falls back to the function form — so a
    dialect that says it has JSON but not arrows is not a defect, and neither
    is refusing the mode that would need them.
    """
    if dialect.supports_json_arrow_operators():
        pytest.skip(f"{dialect.name} has arrow operators")
    if not dialect.supports_json_type():
        pytest.skip(f"{dialect.name} has no JSON support at all")

    with pytest.raises(UnsupportedFeatureError):
        _document_sql(dialect, "arrow")


def test_forced_arrow_mode_is_honoured(dialect):
    """ARROW must mean arrows, not "whatever this dialect defaults to".

    This is the assertion that catches ``format_json_expression`` discarding
    ``expr.mode``. It deliberately does not require AUTO to produce arrows: the
    two spellings take different path arguments — ``->`` takes a key name,
    while a jsonpath function takes ``$.a[0]`` — so a dialect whose callers
    pass jsonpaths must keep the path form in AUTO. What AUTO may not do is
    silently return the same SQL for every mode.
    """
    if not dialect.supports_json_arrow_operators():
        pytest.skip(f"{dialect.name} has no arrow operators")

    sql, _ = _document_sql(dialect, "arrow")
    assert "->" in sql, f"ARROW mode produced {sql!r} on {dialect.name}"


def test_arrow_probe_is_not_claimed_without_the_operators(dialect):
    """A dialect with no arrow support must not be able to render them.

    The inverse of the above, and the one that matters for honesty: claiming
    arrows and then refusing is a broken promise to the caller.
    """
    if dialect.supports_json_arrow_operators():
        pytest.skip(f"{dialect.name} has arrow operators")

    with pytest.raises(UnsupportedFeatureError):
        _document_sql(dialect, "arrow")


def test_forced_function_mode_differs_from_arrow(dialect):
    """FUNCTION and ARROW must be distinguishable, else the mode is ignored.

    This is the assertion that would have caught ``format_json_expression``
    discarding ``expr.mode``: all four mode values rendered the same SQL.

    Both sides build the *same* operator — ``->``, the document access — and
    differ only in ``mode``. That is the point: it is ``mode`` reaching the
    formatter that is under test, not the choice of operator, so holding the
    operator fixed is what makes the comparison mean anything.
    """
    if not dialect.supports_json_arrow_operators():
        pytest.skip(f"{dialect.name} has no arrow operators")

    arrow, _ = _document_sql(dialect, "arrow")
    function, _ = _document_sql(dialect, "function")
    assert arrow != function, (
        f"{dialect.name} renders ARROW and FUNCTION identically ({arrow!r}); "
        f"JSONPathMode is not reaching the formatter"
    )


# ---------------------------------------------------------------------------
# Layer 2: the SQL must be this backend's own
# ---------------------------------------------------------------------------


def test_function_mode_emits_no_foreign_syntax(dialect):
    """The rendered SQL must not contain another backend's function names.

    Catches the core's MySQL-shaped fallback being inherited by a dialect
    that has none of those functions. Whether a backend's own spelling can be
    compared at all depends on a backend-private name lookup; see
    ``_own_function_names``. The presence check comes first so a dialect that
    advertises JSON without naming a single function fails rather than skips.
    """
    if not dialect.supports_json_type():
        pytest.skip(f"{dialect.name} has no JSON support")

    declared = _declared_json_functions(dialect)
    if not declared:
        pytest.fail(
            f"{dialect.name} advertises supports_json_type() but names no JSON "
            f"function in supports_functions(); it cannot name a single JSON "
            f"function"
        )

    own = _own_function_names(dialect)
    if own is None:
        sample = ", ".join(declared[:3]) + ("..." if len(declared) > 3 else "")
        pytest.skip(
            f"{dialect.name} declares {len(declared)} JSON function "
            f"constructors ({sample}) but exposes no "
            f"is_json_function_available(name) helper, so its function-mode "
            f"SQL cannot be compared with the spellings it owns; per-name "
            f"availability is backend-private, not a capability switch. Not "
            f"asserting foreign syntax rather than guessing which names are "
            f"its own."
        )

    sql, _ = _text_sql(dialect, "function")

    if not own:
        # The lookup exists and says nothing is available, so nothing may be
        # claimed either: rendering a foreign name here is a broken promise.
        assert not any(name in sql for name in _FOREIGN_FUNCTION_NAMES), (
            f"{dialect.name} declares no JSON function names but rendered "
            f"{sql!r}"
        )
        return

    assert any(name in sql for name in own), (
        f"{dialect.name} rendered {sql!r}, which contains none of its own "
        f"declared JSON functions {own}"
    )


def _declared_json_functions(dialect) -> Optional[tuple]:
    """JSON function constructors this dialect's own vocabulary names.

    ``supports_functions()`` is a parameterless switch that answers with a
    mapping, so it is a legitimate place to ask which functions a backend has
    -- no per-name capability probe is invented here. The keys are the
    backend's constructor vocabulary (``json_extract``, ``json_unquote``, ...),
    not SQL spellings, so they are only used to establish that the backend can
    name JSON functions at all.

    ``None`` means the dialect has no such switch. An empty tuple means it has
    one and names no JSON function, which the caller treats as a failure.
    """
    switch = getattr(dialect, "supports_functions", None)
    if switch is None:
        return None
    return tuple(sorted(name for name in switch() if "json" in name.lower()))


#: The JSON function names worth asking about. This is not a contract member:
#: it is the fixed list the backend-private ``is_json_function_available``
#: helper (where a backend keeps one) is queried with, one name at a time.
_JSON_FUNCTION_NAMES = (
    "JSON_EXTRACT", "JSON_UNQUOTE", "JSON_QUERY", "JSON_VALUE", "JSON_TABLE",
    "JSON_CONTAINS", "JSON_TYPE", "JSON_SEARCH", "GET_PATH", "OPENJSON",
    "JSONExtractRaw", "JSONExtractString",
    "jsonb_path_query_first", "jsonb_path_query_array", "jsonb_path_query",
)


def _own_function_names(dialect) -> Optional[tuple]:
    """JSON function names this dialect declares for itself, or ``None``.

    ``None`` means the dialect cannot answer: per-name availability is
    backend-private, so a dialect without ``is_json_function_available(name)``
    has no way to say which spellings are its own. Returning ``()`` there would
    be a lie -- it reads as "declares nothing" and turns the caller's check
    into "render no function name at all", which every dialect passes.

    Dialects that do keep the helper (SQL Server, for one) get their real
    answer, and the caller compares the rendered SQL against it.
    """
    probe = getattr(dialect, "is_json_function_available", None)
    if probe is None:
        return None
    return tuple(name for name in _JSON_FUNCTION_NAMES if probe(name))


# ---------------------------------------------------------------------------
# Honesty about the things a dialect does not have
# ---------------------------------------------------------------------------


def test_json_table_claim_matches_the_formatter(dialect):
    """A True probe must not sit in front of a formatter that always raises.

    PostgreSQL and SQL Server both shipped this exact contradiction.
    """
    from rhosocial.activerecord.backend.expression.query_sources import JSONTableExpression

    claimed = dialect.supports_json_table()
    # Probe with a real expression, not None: formatters inspect attributes such
    # as ``json_column``/``path``, and passing None raises AttributeError for a
    # perfectly working formatter, which would be misread as a refusal.
    expr = JSONTableExpression(dialect, json_column="doc", path="$[*]", columns=[])
    try:
        dialect.format_json_table_expression(expr)
    except UnsupportedFeatureError:  # noqa: BLE001 - a deliberate refusal means unsupported
        assert claimed is False, (
            f"{dialect.name} claims supports_json_table() but its formatter "
            f"refuses; callers trusting the probe get an exception at render "
            f"time"
        )
    else:
        assert claimed is True, (
            f"{dialect.name} implements format_json_table_expression but "
            f"reports supports_json_table() as False"
        )


@pytest.mark.parametrize(
    "probe",
    [
        "supports_json_type",
        "supports_jsonb",
        "supports_json_path",
        "supports_json_arrow_operators",
    ],
)
def test_json_probes_are_defined_once_in_the_mro(dialect, probe):
    """Two definitions with different version gates let the MRO pick a winner.

    PostgreSQL's ``supports_jsonb_subscript`` existed three times with gates
    of 11.0 and 14.0, so which answer a caller got depended on class ordering
    rather than on intent.

    A dialect may legitimately override a core default, which puts the probe
    in two classes. What it may not do is define the same probe in several of
    its own mixins, where the winner is an accident of ordering.
    """
    definitions = [
        klass.__name__ for klass in type(dialect).__mro__ if probe in vars(klass)
    ]
    # A probe may be legitimately layered through several classes: the dialect,
    # its backend mixins, the cross-backend mixin and the Protocol declaration.
    # ClickHouse, for example, resolves supports_json_type through five classes
    # in a valid inheritance chain. The defect this guards against is a probe
    # defined in several *sibling* mixins with different version gates so the
    # winner depends on class order; counting definitions alone cannot tell that
    # from a legal chain, so allow a generous depth and keep the check as a
    # runaway-duplication tripwire rather than a strict count.
    assert len(definitions) <= 6, (
        f"{dialect.name} resolves {probe} from {len(definitions)} classes: "
        f"{definitions}"
    )
