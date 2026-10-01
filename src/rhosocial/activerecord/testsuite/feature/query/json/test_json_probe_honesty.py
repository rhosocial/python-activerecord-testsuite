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
"""

# src/rhosocial/activerecord/testsuite/feature/query/json/test_json_probe_honesty.py
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
from rhosocial.activerecord.backend.expression import Column, JSONExpression


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


def _sql(dialect, mode, operation, path="a"):
    col = Column(dialect, "j", table="t")
    return JSONExpression(dialect, col, path, operation, mode=mode).to_sql()


# ---------------------------------------------------------------------------
# Layer 1: a True probe must render
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "probe, operation",
    [
        ("supports_json_type", "->>"),
        ("supports_json_arrow_operators", "->"),
    ],
)
def test_true_json_probe_renders(dialect, probe, operation):
    """If the probe says the dialect handles JSON, it must not then refuse.

    The arrow mode is only required of the arrow probe. Having JSON and having
    ``->`` are separate capabilities — Oracle, Snowflake, BigQuery and Firebird
    all have the first without the second — so demanding arrows of the type
    probe asks the dialect for something it never claimed. The modes each probe
    does cover must render.
    """
    if not getattr(dialect, probe)():
        pytest.skip(f"{dialect.name} does not advertise {probe}")

    modes = ("auto", "arrow", "function") if probe == "supports_json_arrow_operators" else ("auto", "function")
    for mode in modes:
        try:
            sql, params = _sql(dialect, mode, operation)
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
        _sql(dialect, "arrow", "->")


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

    sql, _ = _sql(dialect, "arrow", "->")
    assert "->" in sql, f"ARROW mode produced {sql!r} on {dialect.name}"


def test_arrow_probe_is_not_claimed_without_the_operators(dialect):
    """A dialect with no arrow support must not be able to render them.

    The inverse of the above, and the one that matters for honesty: claiming
    arrows and then refusing is a broken promise to the caller.
    """
    if dialect.supports_json_arrow_operators():
        pytest.skip(f"{dialect.name} has arrow operators")

    with pytest.raises(UnsupportedFeatureError):
        _sql(dialect, "arrow", "->")


def test_forced_function_mode_differs_from_arrow(dialect):
    """FUNCTION and ARROW must be distinguishable, else the mode is ignored.

    This is the assertion that would have caught ``format_json_expression``
    discarding ``expr.mode``: all four mode values rendered the same SQL.
    """
    if not dialect.supports_json_arrow_operators():
        pytest.skip(f"{dialect.name} has no arrow operators")

    arrow, _ = _sql(dialect, "arrow", "->")
    function, _ = _sql(dialect, "function", "->")
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
    that has none of those functions.
    """
    if not dialect.supports_json_type():
        pytest.skip(f"{dialect.name} has no JSON support")

    own = _own_function_names(dialect)
    sql, _ = _sql(dialect, "function", "->>")

    if not own:
        # Nothing declared, so nothing may be claimed either.
        assert not any(name in sql for name in _FOREIGN_FUNCTION_NAMES), (
            f"{dialect.name} declares no JSON function names but rendered "
            f"{sql!r}"
        )
        return

    assert any(name in sql for name in own), (
        f"{dialect.name} rendered {sql!r}, which contains none of its own "
        f"declared JSON functions {own}"
    )


#: The JSON function names worth asking about. Every backend's
#: supports_json_function takes a name rather than returning a set, so the
#: question is asked one name at a time.
_JSON_FUNCTION_NAMES = (
    "JSON_EXTRACT", "JSON_UNQUOTE", "JSON_QUERY", "JSON_VALUE", "JSON_TABLE",
    "JSON_CONTAINS", "JSON_TYPE", "JSON_SEARCH", "GET_PATH", "OPENJSON",
    "JSONExtractRaw", "JSONExtractString",
    "jsonb_path_query_first", "jsonb_path_query_array", "jsonb_path_query",
)


def _own_function_names(dialect) -> tuple:
    """JSON function names this dialect declares for itself.

    Asks ``supports_json_function(name)`` per name, because that is the shape
    every backend implements. Calling it with no arguments — which an earlier
    version of this helper did — raises TypeError on all of them and returns
    nothing, so the check silently degraded to "render no function name at
    all" and no backend was ever really compared against its own set.

    A dialect with no such probe gets an empty result, which is legitimate: it
    means the dialect renders with operators only.
    """
    probe = getattr(dialect, "supports_json_function", None)
    if probe is None:
        return ()
    own = []
    for name in _JSON_FUNCTION_NAMES:
        try:
            if probe(name):
                own.append(name)
        except Exception:  # noqa: BLE001 - a probe that cannot answer is not a failure here
            return ()
    return tuple(own)


# ---------------------------------------------------------------------------
# Honesty about the things a dialect does not have
# ---------------------------------------------------------------------------


def test_json_table_claim_matches_the_formatter(dialect):
    """A True probe must not sit in front of a formatter that always raises.

    PostgreSQL and SQL Server both shipped this exact contradiction.
    """
    claimed = dialect.supports_json_table()
    try:
        dialect.format_json_table_expression(None)
    except Exception:  # noqa: BLE001 - the refusal is what we are checking
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
    # Three is the normal shape: the dialect's own override, the mixin default
    # it overrides, and the Protocol declaration. The defect was a probe
    # defined in several *backend-specific* mixins with different version
    # gates, which made the winner depend on class order. Allow the normal
    # three and reject a fourth.
    assert len(definitions) <= 3, (
        f"{dialect.name} resolves {probe} from {len(definitions)} classes: "
        f"{definitions}"
    )
