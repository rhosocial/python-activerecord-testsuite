# tests/rhosocial/activerecord/testsuite/feature/basic/fixtures/test_operations.py
"""The fixture registry answers through both dialect channels, or it fails.

The registry exists because core cannot yet say what a declaration needs.
That makes it the one place a capability question can be answered wrongly, so
the resolution order and the strictness around it are tested here rather than
in a backend's suite.
"""
from rhosocial.activerecord.backend.impl.dummy.dialect import DummyDialect
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    Operation,
    TableFixture,
    operation_reason,
    switch_answer,
    table_reason,
)
from rhosocial.activerecord.testsuite.pytest_plugin.requirements import (
    MissingRequirementError,
)

import pytest


class BothChannels(DummyDialect):
    """A method and a concept table, the two channels the real dialects use."""

    name = "BothChannels"

    def supports_identity_column(self):
        return True

    def format_data_type_json(self, expr):
        return ("JSON", ())  # declares the json concept


class MethodOnly(DummyDialect):
    name = "MethodOnly"

    def supports_identity_column(self):
        return False


class Neither(DummyDialect):
    name = "Neither"


def test_a_method_answers_first_and_names_the_answer():
    assert switch_answer(BothChannels(), "supports_identity_column") is True
    assert switch_answer(MethodOnly(), "supports_identity_column") is False


def test_a_concept_key_answers_when_no_method_does():
    assert switch_answer(BothChannels(), "json") is True
    assert switch_answer(BothChannels(), "array") is False


def test_a_switch_that_neither_channel_answers_is_a_gap_not_a_no():
    with pytest.raises(MissingRequirementError, match="Neither.supports_xml"):
        switch_answer(Neither(), "supports_xml")


def test_an_operation_reason_names_the_operation_and_the_switch():
    operation = Operation("insert", requires_on=("array",), column="tags")

    why = operation_reason(BothChannels(), operation)

    assert why is not None
    assert "insert on column tags" in why
    assert "array" in why
    assert "BothChannels" in why


def test_a_switch_required_off_is_honoured():
    operation = Operation("create_table", requires_off=("supports_identity_column",))

    why = operation_reason(BothChannels(), operation)

    assert why is not None
    assert "answer no" in why


def test_a_satisfied_operation_has_no_reason():
    operation = Operation("create_table", requires_on=("json",))

    assert operation_reason(BothChannels(), operation) is None


def test_a_table_names_the_first_operation_that_cannot_run():
    fixture = TableFixture(
        table="t",
        source=None,
        operations=(
            Operation("create_table"),
            Operation("insert", requires_on=("array",)),
        ),
    )

    why = table_reason(BothChannels(), fixture)

    assert why is not None
    assert "insert" in why


def test_a_projection_has_no_operations_to_judge():
    fixture = TableFixture(table="t", source=None)

    assert table_reason(Neither(), fixture) is None
