# src/rhosocial/activerecord/testsuite/feature/rules/test_type_name_contract.py
"""Formal source: the SQL type-name grammar
(``backend/expression/type_name.py``: identifier / qualified / precision /
array forms, plus the closed multi-word set) and the spellings section of
``docs/en_US/backend/expression/types.md``.

A type name is rendered into a grammar position that cannot take a bound
parameter, so safe spelling is a validation question, not a dialect question.
``CustomType`` validates once at construction; every renderer therefore sees a
name the grammar already admitted. The multi-word set is enumerated rather
than allowing spaces, so ``INTEGER, (SELECT ...)`` cannot be spelled.
"""

import pytest

from rhosocial.activerecord.backend.expression.type_name import (
    InvalidTypeNameError,
    is_valid_type_name,
    validate_type_name,
)
from rhosocial.activerecord.backend.expression.types.custom import CustomType

_SAFE = (
    "varchar(255)",
    "numeric(10, 2)",
    "myschema.mytype",
    "text[]",
    "vector",
    "hstore",
    "double precision",
    "timestamp(3) with time zone",
)

_HOSTILE = (
    "varchar(255); DROP TABLE users; --",
    "varchar(255) -- comment",
    "varchar(255) /* comment */",
    "varchar' OR '1'='1",
    '"quoted name"',
    "int, (SELECT password FROM users)",
    "x.y.z",
    "text UNION SELECT 1",
)


@pytest.mark.parametrize("name", _SAFE)
def test_safe_spellings_are_accepted_unchanged(name):
    assert validate_type_name(name) == name
    assert is_valid_type_name(name)


@pytest.mark.parametrize("name", _HOSTILE)
def test_quote_comment_and_injection_shapes_are_refused(name):
    with pytest.raises(InvalidTypeNameError) as exc:
        validate_type_name(name)
    assert name in str(exc.value)
    assert not is_valid_type_name(name)


def test_a_non_string_is_refused_by_the_same_grammar():
    with pytest.raises(InvalidTypeNameError):
        validate_type_name(None)


def test_invalid_type_name_error_is_a_value_error():
    assert issubclass(InvalidTypeNameError, ValueError)


def test_custom_type_validates_before_any_dialect_is_consulted():
    """Six renderers used to emit ``raw`` unchecked; the constructor owns it."""
    assert CustomType(raw="vector(8)").get_params()["raw"] == "vector(8)"
    for name in _HOSTILE:
        with pytest.raises(InvalidTypeNameError):
            CustomType(raw=name)
