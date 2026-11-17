# tests/rhosocial/activerecord/testsuite/pytest_plugin/test_parallel_declaration.py
"""Parallel grouping is declared, never inferred.

A directory pins its tests to one worker only when it declares
``Declaration(parallel=True)``. Having a conftest or using a ``database``
fixture is *not* a declaration; a scope that says nothing runs in unlimited
parallel. This regression test locks that rule down.
"""

from types import SimpleNamespace


from rhosocial.activerecord.testsuite.pytest_plugin import Declaration, hooks


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
