# testsuite/feature/query/typed_column/test_enum_capability_contracts.py
"""What a backend says about the generic ``enum`` type.

The core has an ``EnumType`` and no backend implemented a formatter for it, so
a model declaring an enumerated field failed everywhere. Two things have to
hold afterwards, and they pull in opposite directions:

* A backend that can render it must say so. Claiming support without a
  formatter, or staying silent about a type the backend renders natively, both
  leave the caller to guess.
* A backend that cannot must name a substitute it *can* render. A suggestion
  pointing at a type the dialect has no formatter for is no suggestion: the
  swap fails the same way.

Neither set may overlap, because a type in both is one of the two a lie.
"""

# testsuite/feature/query/typed_column/test_enum_capability_contracts.py
import pytest

from rhosocial.activerecord.backend.expression.types import EnumType


def _renderable(dialect) -> set:
    """The generic type names this dialect can actually render."""
    return set(dialect.supports_data_types())


def _suggested(dialect) -> dict:
    return dialect.suggested_data_types() or {}


def test_supported_and_suggested_are_disjoint(dialect):
    """A name in both is one of the two being a lie."""
    overlap = sorted(_renderable(dialect) & set(_suggested(dialect)))
    assert not overlap, (
        f"{dialect.name} both renders and suggests a substitute for {overlap}; "
        f"a suggestion exists for a type the dialect cannot render"
    )


def test_an_advertised_enum_really_renders(dialect):
    """``supports_data_types`` is read as a promise about DDL generation."""
    if "enum" not in _renderable(dialect):
        pytest.skip(f"{dialect.name} does not advertise the generic enum type")
    sql, _ = dialect.format_data_type(EnumType(dialect, ["a", "b"]))
    assert sql, f"{dialect.name} advertised enum and rendered nothing"


def test_an_advertised_enum_lists_its_values(dialect):
    """The values are the whole point; a bare ENUM() has lost them."""
    if "enum" not in _renderable(dialect):
        pytest.skip(f"{dialect.name} does not advertise the generic enum type")
    sql, _ = dialect.format_data_type(EnumType(dialect, ["draft", "live"]))
    assert "draft" in sql and "live" in sql, sql


def test_a_suggested_substitute_is_renderable_here(dialect):
    """The suggestion is the only route forward, so it has to work.

    SQL Server suggested EnumType for enum, which is the type it cannot
    render: swapping one for the other failed identically and the caller was
    sent round in circles with what looked like advice.
    """
    substitute = _suggested(dialect).get("enum")
    if substitute is None:
        pytest.skip(f"{dialect.name} suggests nothing for enum")
    assert substitute is not EnumType, (
        f"{dialect.name} suggests EnumType for enum, which it cannot render"
    )
    assert "enum" not in _renderable(dialect) or substitute is not EnumType


def test_a_substitute_renders_on_this_dialect(dialect):
    substitute = _suggested(dialect).get("enum")
    if substitute is None:
        pytest.skip(f"{dialect.name} suggests nothing for enum")
    instance = substitute(dialect)
    if instance.name == "enum":
        # The substitute carries its own name, so it dispatches on its own
        # formatter rather than this one.
        pytest.skip(f"{dialect.name} substitutes its own enum type")
    try:
        rendered = dialect.format_data_type(instance)
    except TypeError as exc:
        pytest.fail(f"{dialect.name} suggests {substitute.__name__} but cannot render it: {exc}")
    assert rendered[0]


def test_refusing_an_enum_names_the_substitute(dialect):
    """The message is the only place the answer reaches a caller."""
    substitute = _suggested(dialect).get("enum")
    if substitute is None or "enum" in _renderable(dialect):
        pytest.skip(f"{dialect.name} does not refuse the generic enum type")
    with pytest.raises(TypeError) as excinfo:
        dialect.format_data_type(EnumType(dialect, ["a"]))
    assert substitute.__name__ in str(excinfo.value), (
        f"{dialect.name} refuses enum without naming {substitute.__name__}: "
        f"{excinfo.value}"
    )
