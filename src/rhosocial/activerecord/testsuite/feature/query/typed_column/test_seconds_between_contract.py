# testsuite/feature/query/typed_column/test_seconds_between_contract.py
"""The ``seconds_between`` surface every backend inherits from the core.

How the value is rendered belongs to the dialect: PostgreSQL subtracts two
timestamps into an interval, SQLite multiplies a julian-day difference, MySQL
counts in a named unit. Each backend pins its own spelling in its own
repository, against its own engine.

What is shared, and therefore asserted here, is the answer shape: a timestamp
column and the factory build the same node, the node is a number, the operands
keep the order the caller wrote them in, and an alias survives. A backend that
satisfies these inherits the semantics -- ``end - start`` in seconds -- from
the core; only the SQL around them is its own.

Rendering is deliberately not exercised. A backend that has not adapted the
formatter yet raises ``UnsupportedFeatureError`` by design, and a contract run
by such a backend would report the backend's honest refusal as a failure.
"""

# testsuite/feature/query/typed_column/test_seconds_between_contract.py
from rhosocial.activerecord.backend.expression import seconds_between
from rhosocial.activerecord.backend.expression.datetime import SecondsBetweenExpression
from rhosocial.activerecord.backend.expression.value_types import NumericValue


def test_the_column_offers_seconds_between(json_user_fixture):
    """A datetime field and a factory build the same kind of node."""
    model = json_user_fixture
    created = model.c.created_at
    updated = model.c.updated_at

    from_column = created.seconds_between(updated)
    from_factory = seconds_between(model.__backend__.dialect, created, updated)

    assert isinstance(from_column, SecondsBetweenExpression)
    assert isinstance(from_factory, SecondsBetweenExpression)


def test_the_operands_keep_the_callers_order(json_user_fixture):
    """``start`` and ``end`` are not interchangeable: the sight of the sign is."""
    model = json_user_fixture
    created = model.c.created_at
    updated = model.c.updated_at

    expression = created.seconds_between(updated)

    assert expression.start is created
    assert expression.end is updated


def test_the_result_is_a_number(json_user_fixture):
    """Seconds are divisible, so the result is numeric rather than temporal."""
    model = json_user_fixture
    expression = model.c.created_at.seconds_between(model.c.updated_at)

    assert isinstance(expression, NumericValue)
    assert not hasattr(expression, "date_trunc"), "a duration is not a point in time"


def test_an_alias_survives(json_user_fixture):
    """The alias decorates the rendered value, as everywhere else."""
    model = json_user_fixture
    expression = model.c.created_at.seconds_between(model.c.updated_at).as_("elapsed")

    assert expression.alias == "elapsed"
