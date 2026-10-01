# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_uuid_capability_contracts.py
"""UUID capabilities must be consistent, and honest when absent.

Storage and generation are separate concerns. ``UUIDType`` says how a value
is stored; ``UUIDSupport`` says whether the database can produce one. A
backend that advertises generation and then emits another backend's function
is worse than one that admits it cannot, because the caller's query fails at
runtime instead of at capability-check time.

No live database is needed: every assertion is on rendered SQL.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_uuid_capability_contracts.py
import pytest

from rhosocial.activerecord.testsuite.feature.query.conftest import (
    json_user_fixture,
)

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
from rhosocial.activerecord.backend.expression import (
    Literal,
    UUIDCastExpression,
    UUIDConstantExpression,
    UUIDGenerationExpression,
)


_NIL = "00000000-0000-0000-0000-000000000000"
_MAX = "ffffffff-ffff-ffff-ffff-ffffffffffff"


# ---------------------------------------------------------------------------
# Probe / implementation agreement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "probe, factory",
    [
        ("supports_uuid_generation", lambda d: UUIDGenerationExpression(d)),
        ("supports_uuid_constant", lambda d: UUIDConstantExpression(d, "nil")),
        ("supports_uuid_cast", lambda d: UUIDCastExpression(d, Literal(d, "x"))),
    ],
    ids=["generation", "constant", "cast"],
)
def test_supported_uuid_operation_renders(dialect, probe, factory):
    """A True probe must render, not refuse."""
    if not getattr(dialect, probe)():
        pytest.skip(f"{dialect.name} does not advertise {probe}")

    sql, params = factory(dialect).to_sql()
    assert sql, f"{dialect.name} advertised {probe} but rendered nothing"


@pytest.mark.parametrize(
    "probe, factory",
    [
        ("supports_uuid_generation", lambda d: UUIDGenerationExpression(d)),
        ("supports_uuid_constant", lambda d: UUIDConstantExpression(d, "nil")),
        ("supports_uuid_cast", lambda d: UUIDCastExpression(d, Literal(d, "x"))),
    ],
    ids=["generation", "constant", "cast"],
)
def test_unsupported_uuid_operation_refuses(dialect, probe, factory):
    """A False probe must refuse, rather than emit a guess.

    Refusing is the whole value of an honest probe: the caller can pick
    another route instead of shipping SQL the server will reject.
    """
    if getattr(dialect, probe)():
        pytest.skip(f"{dialect.name} advertises {probe}")

    with pytest.raises(UnsupportedFeatureError):
        factory(dialect).to_sql()


def test_refusal_carries_a_suggestion(dialect):
    """An error the caller cannot act on is only marginally better than wrong SQL."""
    if dialect.supports_uuid_generation():
        pytest.skip(f"{dialect.name} can generate UUIDs")

    with pytest.raises(UnsupportedFeatureError) as excinfo:
        UUIDGenerationExpression(dialect).to_sql()

    suggestion = str(excinfo.value)
    assert "uuid" in suggestion.lower(), (
        f"{dialect.name} refusal names no route forward: {suggestion!r}"
    )


# ---------------------------------------------------------------------------
# No cross-backend leakage
# ---------------------------------------------------------------------------


def test_generation_emits_no_other_backends_function(dialect):
    """Each backend's generator is its own; borrowing one fails at runtime."""
    if not dialect.supports_uuid_generation():
        pytest.skip(f"{dialect.name} cannot generate UUIDs")

    sql, _ = UUIDGenerationExpression(dialect).to_sql()
    foreign = {
        "Postgres": ("uuid_generate_v1", "uuid_generate_v4"),
        "SQLServer": ("NEWID", "NEWSEQUENTIALID"),
        "MySQL": ("UUID()",),
        "MariaDB": ("UUID()",),
        "Oracle": ("SYS_GUID()",),
        "Snowflake": ("UUID_STRING()",),
        "BigQuery": ("GENERATE_UUID()",),
        "ClickHouse": ("generateUUIDv4",),
        "Firebird": ("GEN_UUID()",),
    }
    borrowed = foreign.get(dialect.name, ())
    for name in borrowed:
        assert name.lower() not in sql.lower(), (
            f"{dialect.name} rendered {sql!r}, which is another backend's "
            f"generator ({name})"
        )


def test_generation_is_aliasable(dialect):
    if not dialect.supports_uuid_generation():
        pytest.skip(f"{dialect.name} cannot generate UUIDs")

    sql, _ = UUIDGenerationExpression(dialect, alias="u").to_sql()
    ident = dialect.format_identifier("u")
    assert sql.endswith(f"AS {ident}")
    assert sql.startswith(ident) is False, "the alias must not replace the expression"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("which, value", [("nil", _NIL), ("max", _MAX)])
def test_constants_carry_the_right_value(dialect, which, value):
    """The literal must be in the statement, not only in Python.

    A constant that renders as a placeholder would compare every row against
    NULL.
    """
    if not dialect.supports_uuid_constant():
        pytest.skip(f"{dialect.name} has no UUID constants")

    sql, _ = UUIDConstantExpression(dialect, which).to_sql()
    assert value in sql, f"{dialect.name} rendered {sql!r} without the {which} value"


def test_unknown_constant_kind_is_rejected(dialect):
    """A typo must not silently render something else."""
    with pytest.raises(ValueError, match="which must be one of"):
        UUIDConstantExpression(dialect, "middle")


# ---------------------------------------------------------------------------
# Cast
# ---------------------------------------------------------------------------


def test_cast_keeps_its_parameters(dialect):
    """The operand must stay bound, not be inlined into the statement."""
    if not dialect.supports_uuid_cast():
        pytest.skip(f"{dialect.name} cannot cast to UUID")

    expr = UUIDCastExpression(dialect, Literal(dialect, "not-a-uuid"))
    sql, params = expr.to_sql()
    assert params == ("not-a-uuid",)
    assert "not-a-uuid" not in sql, f"{dialect.name} inlined the operand: {sql!r}"


# ---------------------------------------------------------------------------
# Storage is a separate concern from generation
# ---------------------------------------------------------------------------


def test_storage_capability_is_declared_independently(dialect):
    """A backend may store UUIDs without being able to generate them.

    SQLite is the motivating case: it stores a UUID fine as text and has no
    UUID function at all, so the two probes must be allowed to disagree.
    """
    from rhosocial.activerecord.backend.expression.types import UUIDType

    supported = dialect.supports_data_types()
    suggested = dialect.suggested_data_types()
    stores_natively = "uuid" in supported
    has_substitute = "uuid" in suggested

    assert stores_natively != has_substitute, (
        f"{dialect.name} both renders the uuid type and suggests a substitute "
        f"for it; a suggestion exists for types the dialect cannot render"
    )
    if not stores_natively and not has_substitute:
        pytest.skip(f"{dialect.name} declares no UUID storage at all")

    if stores_natively:
        rendered = dialect.format_data_type(UUIDType())
        assert rendered[0]
