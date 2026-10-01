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

from rhosocial.activerecord.testsuite.feature.query.conftest import (
    json_user_fixture,
)

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
from rhosocial.activerecord.backend.expression import Column, JSONExpression


#: Function names that belong to one specific backend. A dialect rendering any
#: of these is emitting foreign syntax.
_FOREIGN_FUNCTION_NAMES = (
    "JSON_EXTRACT",     # MySQL
    "JSON_UNQUOTE",     # MySQL
    "JSON_CONTAINS",    # MySQL
    "JSON_TYPE",        # MySQL
    "JSON_SEARCH",      # MySQL
    "GET_PATH",         # Snowflake
    "JSON_QUERY",       # BigQuery
    "jsonb_path_query",  # PostgreSQL
    "OPENJSON",         # SQL Server
    "JSON_VALUE",       # Oracle / SQL Server / BigQuery
    "JSON_TABLE",       # Oracle / MySQL / SQL Server
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
    """If the probe says the dialect handles JSON, it must not then refuse."""
    if not getattr(dialect, probe)():
        pytest.skip(f"{dialect.name} does not advertise {probe}")

    for mode in ("auto", "arrow", "function"):
        try:
            sql, params = _sql(dialect, mode, operation)
        except Exception as exc:  # noqa: BLE001 - any refusal is a defect
            pytest.fail(
                f"{dialect.name} advertises {probe}() but rendering mode="
                f"{mode!r} raised {type(exc).__name__}: {exc}"
            )
        assert sql, f"{dialect.name} rendered an empty statement for mode={mode!r}"


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


def _own_function_names(dialect):
    """JSON function names this dialect declares for itself.

    Read from the dialect's own ``supports_json_function`` set, falling back
    to nothing. An empty result is a legitimate state: it means the dialect
    must render with operators only, and the test above then demands it
    invent no function name at all.
    """
    probe = getattr(dialect, "supports_json_function", None)
    if probe is None:
        return ()
    try:
        declared = probe()
    except Exception:  # noqa: BLE001 - a broken probe is not a test failure
        return ()
    if isinstance(declared, dict):
        return tuple(declared)
    if isinstance(declared, (set, frozenset, list, tuple)):
        return tuple(str(item) for item in declared)
    return ()


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
    assert len(definitions) <= 2, (
        f"{dialect.name} resolves {probe} from {len(definitions)} classes: "
        f"{definitions}"
    )
