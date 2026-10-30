# src/rhosocial/activerecord/testsuite/pytest_compat.py
"""Compatibility shims for pytest plugins that have not caught up with 9.2.

pytest 9.2.0 (2026-10-27) moved a node's identifier into a structured
``NodeId``. The public ``nodeid`` is unchanged and remains the supported
surface, but two plugins in this toolchain still touch the private storage:

* ``pytest-benchmark`` 5.3.0 -- the newest release -- reads ``node._nodeid``
  when it builds its fixture, so every benchmark test errors at setup with
  ``'Function' object has no attribute '_nodeid'`` (upstream issue #321).
* ``pytest-xdist`` 3.8.0 -- also the newest -- writes the ``--dist=loadgroup``
  suffix into ``item._nodeid``, which 9.2 no longer reads, so ``xdist_group``
  markers are silently ignored and grouped tests spread across workers
  (upstream PR #1388 is merged but unreleased).

Both shims are deliberately narrow: they restore the old storage for the
plugin that still uses it and change nothing else -- no identifier, no report
name, no selection. Each is guarded so it is a no-op on pytest < 9.2, and each
becomes inert once its plugin is fixed, at which point the function is deleted
rather than kept as folklore.

The module is registered as a ``pytest11`` entry point, so it loads wherever
this test suite is installed; the backend files it protects are the same ones.
"""

import pytest


def pytest_collection_finish(session):
    """Give ``pytest-benchmark`` back the private ``node._nodeid`` it reads.

    The value is the public ``nodeid`` verbatim, so nothing downstream changes:
    the only consumer is the plugin's fixture, which wants a name to report.
    """
    for item in session.items:
        if not hasattr(item, "_nodeid"):
            try:
                item._nodeid = item.nodeid
            except AttributeError:  # a node class that refuses the attribute
                pass


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """Carry the ``--dist=loadgroup`` suffix into the field pytest 9.2 reads.

    ``pytest-xdist`` appends ``@<group>`` to ``item._nodeid``; pytest 9.2 reads
    ``item._id``. Running ``trylast`` means this sees what xdist wrote, and
    copying it into ``_id`` is the whole fix. On pytest < 9.2 the import below
    fails and the function does nothing.
    """
    try:
        from _pytest.nodeid import coerce_node_id  # pytest >= 9.2 only
    except ImportError:
        return

    for item in items:
        wanted = item.__dict__.get("_nodeid")
        if isinstance(wanted, str) and wanted != item.nodeid:
            item._id = coerce_node_id(wanted)
