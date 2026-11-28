# tests/test_contract_naming.py
"""The namespace rules' own controls: synthetic subjects, no real backend.

These prove that the shared rule functions can fail. They belong here, in the
testsuite's own tests, rather than in the rule module every backend imports: a
backend should run the rules that judge it, not the controls that judge the rule
implementation, and a control that runs in ten places is ten chances to read it
as a contract.

Every synthetic owner is made up (``Probe``, ``ProbeThing``). Borrowing a real
backend's name for the sample would reintroduce, in the control, exactly the
knowledge the rules are written not to have.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.testsuite.feature.rules.contracts import naming, ownership
from rhosocial.activerecord.testsuite.feature.rules.contracts.subject import (
    ExpressionSubject,
    Root,
)

NODE_SOURCE = """
from rhosocial.activerecord.backend.expression.bases import BaseExpression


class {name}(BaseExpression):
    @property
    def format_method(self) -> str:
        return "format_{kind}"
"""


def write_node(root: Path, relative: str, name: str) -> None:
    """Write one synthetic node at *relative* below *root*."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(NODE_SOURCE.format(name=name, kind=name.lower()), encoding="utf-8")


def owned_subject(root: Path, prefix: str = "Probe") -> ExpressionSubject:
    """A subject that owns vocabulary, over a synthetic tree."""
    return ExpressionSubject(
        label="probe-owner",
        roots=(Root("probe", root, "probe.pkg"),),
        prefix=prefix,
        open_package_root=root,
    )


def generic_subject(root: Path) -> ExpressionSubject:
    """The generic side: no prefix, ``impl`` excluded."""
    return ExpressionSubject(
        label="probe-generic",
        roots=(Root("probe", root, "probe.pkg"),),
        excluded_dirs=("impl",),
        open_package_root=root,
    )


def test_a_node_in_the_expression_package_is_clean(tmp_path: Path) -> None:
    write_node(tmp_path, "expression/thing.py", "ProbeThing")
    subject = owned_subject(tmp_path)
    assert not naming.placement_offenders(subject)
    assert not ownership.naming_offenders(subject)


def test_a_node_outside_the_expression_package_is_flagged(tmp_path: Path) -> None:
    write_node(tmp_path, "helper.py", "ProbeHelper")
    problems = naming.placement_offenders(owned_subject(tmp_path))
    assert problems and "outside the expression namespace" in problems[0]


def test_a_node_without_the_owner_prefix_is_flagged(tmp_path: Path) -> None:
    write_node(tmp_path, "expression/thing.py", "OtherThing")
    problems = ownership.naming_offenders(owned_subject(tmp_path))
    assert problems and "does not start with Probe" in problems[0]


def test_a_node_reusing_a_core_name_is_flagged(tmp_path: Path) -> None:
    write_node(tmp_path, "expression/thing.py", "Parameter")
    problems = ownership.naming_offenders(owned_subject(tmp_path))
    assert any("reuses a core expression name" in problem for problem in problems)


def test_the_generic_side_has_no_prefix_claim(tmp_path: Path) -> None:
    """The generic side owns the vocabulary, so it is neither prefixed nor exempted."""
    write_node(tmp_path, "expression/thing.py", "AnyNameAtAll")
    subject = generic_subject(tmp_path)
    assert not naming.placement_offenders(subject)
    with pytest.raises(AssertionError):
        ownership.naming_offenders(subject)


def test_a_closed_namespace_root_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "__init__.py").write_text("", encoding="utf-8")
    assert naming.open_package_offenders(owned_subject(tmp_path))


def test_an_open_namespace_root_is_clean(tmp_path: Path) -> None:
    (tmp_path / "expression").mkdir()
    assert not naming.open_package_offenders(owned_subject(tmp_path))


def test_an_abstract_base_is_not_a_node(tmp_path: Path) -> None:
    base = tmp_path / "expression" / "base.py"
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_text(
        "from abc import ABC, abstractmethod\n"
        "from rhosocial.activerecord.backend.expression.bases import BaseExpression\n"
        "\n"
        "class ProbeRange(BaseExpression, ABC):\n"
        "    @property\n"
        "    @abstractmethod\n"
        "    def format_method(self) -> str:\n"
        "        raise NotImplementedError\n",
        encoding="utf-8",
    )
    write_node(tmp_path, "expression/split.py", "ProbeSplit")
    names = {name for _, _, name in naming.nodes(owned_subject(tmp_path))}
    assert "ProbeSplit" in names
    assert "ProbeRange" not in names


def test_an_excluded_tree_is_not_scanned(tmp_path: Path) -> None:
    """``impl`` is out of scope for the generic subject: it is not its vocabulary."""
    write_node(tmp_path, "impl/other/expression/thing.py", "OtherThing")
    subject = generic_subject(tmp_path)
    assert not naming.nodes(subject)
    assert not naming.placement_offenders(subject)
