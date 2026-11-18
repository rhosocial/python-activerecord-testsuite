# tests/rhosocial/activerecord/testsuite/pytest_plugin/test_parallel_declaration.py
"""Parallel grouping is declared, never inferred.

A directory pins its tests to one worker only when it declares
``Declaration(parallel=True)``. Having a conftest or using a ``database``
fixture is *not* a declaration; a scope that says nothing runs in unlimited
parallel. This regression test locks that rule down.
"""

from pathlib import Path
from types import SimpleNamespace

from rhosocial.activerecord.testsuite.pytest_plugin import Declaration, hooks
from rhosocial.activerecord.testsuite.pytest_plugin.declarations import (
    declaration_for,
)


def _item(path_str, declaration):
    """A minimal pytest item with a path and a marker collector."""
    markers = []
    item = SimpleNamespace(
        path=SimpleNamespace(__fspath__=lambda: path_str),
        add_marker=lambda m: markers.append(m),
        user_properties=[],
        _markers=markers,
    )
    return item, markers


def _run_collection(monkeypatch, tmp_path, declaration):
    """Call collection_modifyitems for one item under a conftest declaring *declaration*."""
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("", encoding="utf-8")

    def fake_declaration_for(pluginmanager, path):
        return declaration

    monkeypatch.setattr(hooks, "declaration_for", fake_declaration_for)
    monkeypatch.setattr(hooks, "scenario_name", lambda item: "default_scenario")
    monkeypatch.setattr(hooks, "attach_text", lambda item, decl: None)

    item, markers = _item(str(test_file), declaration)
    config = SimpleNamespace(pluginmanager=object())
    hooks.collection_modifyitems(config, [item])
    return markers


def test_declared_parallel_pins_to_one_worker(monkeypatch, tmp_path):
    """Declaration(parallel=True) adds an xdist_group marker."""
    decl = Declaration(parallel=True)
    markers = _run_collection(monkeypatch, tmp_path, decl)
    groups = [m for m in markers if getattr(m, "name", "") == "xdist_group"]
    assert len(groups) == 1


def test_no_declaration_runs_unrestricted(monkeypatch, tmp_path):
    """No declaration means no xdist_group, even for a test whose file exists."""
    markers = _run_collection(monkeypatch, tmp_path, None)
    groups = [m for m in markers if getattr(m, "name", "") == "xdist_group"]
    assert groups == []


def test_declaration_false_runs_unrestricted(monkeypatch, tmp_path):
    """Declaration(parallel=False) explicitly opts out of grouping."""
    markers = _run_collection(monkeypatch, tmp_path, Declaration(parallel=False))
    groups = [m for m in markers if getattr(m, "name", "") == "xdist_group"]
    assert groups == []


# --- declaration_for: the nearest declaration at or above a test file --------
# The developer decides the smallest parallel unit by putting DECLARATION in a
# directory's conftest; deeper directories inherit it. These use the real
# declaration_for (no mock) over a temporary conftest tree.


def _pluginmanager_with_conftests(*conftest_dirs):
    """A pluginmanager stub whose plugins are the given conftest dirs."""
    plugins = []
    for directory, declaration in conftest_dirs:
        module = SimpleNamespace(__file__=str(Path(directory) / "conftest.py"))
        if declaration is not None:
            module.DECLARATION = declaration
        plugins.append(module)
    return SimpleNamespace(get_plugins=lambda: plugins)


def test_declaration_found_at_the_test_directory(tmp_path):
    """A conftest declaring parallel in the test's own directory applies."""
    decl = Declaration(parallel=True)
    pm = _pluginmanager_with_conftests((tmp_path, decl))
    test_file = tmp_path / "test_sample.py"
    assert declaration_for(pm, test_file) is decl


def test_declaration_inherited_from_a_parent_directory(tmp_path):
    """A deeper test with no conftest of its own inherits the parent declaration."""
    decl = Declaration(parallel=True)
    deep = tmp_path / "sub" / "deep"
    deep.mkdir(parents=True)
    pm = _pluginmanager_with_conftests((tmp_path, decl), (deep, None))
    test_file = deep / "test_sample.py"
    assert declaration_for(pm, test_file) is decl


def test_nearest_declaration_wins(tmp_path):
    """A nearer conftest's declaration overrides the ancestor's."""
    outer = Declaration(parallel=True, purpose="outer")
    inner = Declaration(parallel=False, purpose="inner")
    sub = tmp_path / "sub"
    sub.mkdir()
    pm = _pluginmanager_with_conftests((tmp_path, outer), (sub, inner))
    test_file = sub / "test_sample.py"
    assert declaration_for(pm, test_file) is inner


def test_no_declaration_anywhere_returns_none(tmp_path):
    """An undeclared tree yields None, so collection leaves it unrestricted."""
    pm = _pluginmanager_with_conftests((tmp_path, None))
    test_file = tmp_path / "test_sample.py"
    assert declaration_for(pm, test_file) is None


def test_database_use_is_opt_in():
    """uses_database defaults off; a declaring scope owns the choice."""
    assert Declaration().uses_database is False
    assert Declaration(uses_database=True).uses_database is True


def test_undeclared_database_fixture_fails_collection():
    """Requesting a DB fixture without uses_database raises a UsageError."""
    import pytest

    item = SimpleNamespace(
        nodeid="test_scope.py::test_x",
        fixturenames=["database"],
    )
    declaration = Declaration(parallel=True)  # uses_database not declared
    try:
        hooks._check_database_declaration(item, declaration)
    except pytest.UsageError as exc:
        assert "uses_database=True" in str(exc)
        assert "database" in str(exc)
    else:
        raise AssertionError("undeclared database fixture was not refused")


def test_declared_database_fixture_passes():
    """A scope that declares uses_database may request DB fixtures."""
    item = SimpleNamespace(
        nodeid="test_scope.py::test_x",
        fixturenames=["database", "schema", "database_config"],
    )
    hooks._check_database_declaration(item, Declaration(uses_database=True))
