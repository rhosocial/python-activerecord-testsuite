# src/rhosocial/activerecord/testsuite/feature/basic/expressions/conftest.py
"""L2 environment fixtures for ``basic/expressions`` (README section 12).

This directory asserts on column expressions only -- which class a model
declaration selects on a dialect, and which operations that class offers. It
owns no table and opens no connection: ``TableFixture.source`` is ``None`` for
every table it would name, so there is no ``schema`` fixture and no
``database`` fixture here (README sections 8.1 and 12).

The dialect comes from an *unconnected* backend instance built from the
scenario. ``suggested_column_types()`` is a static declaration answer (README
F4/F12), so no ``introspect_and_adapt()`` is needed to read it. A scenario whose
dialect cannot answer that table without a live backend is skipped by name
(README section 9) instead of quietly connecting.

Models borrow their ``__backend__`` from that unconnected instance so that
``Model.c.<field>`` resolves against the same dialect; the previous value is
restored on teardown. Nothing is written, and no driver is opened.
"""

import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_complex_models import (
    AsyncComplexRow,
    AsyncComplexRowAnnotated,
    ComplexRow,
    ComplexRowAnnotated,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_models import (
    AsyncTypedUser,
    TypedUser,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.user_models import (
    AsyncMappedUser,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    parallel=True,
    purpose="Column expression classes and operation sets under ``basic/expressions``",
    passes_means="each declaration selects the dialect's answered column class and "
    "each family's operation renders",
    fails_means="a column class is hard-coded, an operation is missing, or a dialect "
    "gap is answered silently",
)

#: Existing models only (README section 12: no new models). ``.c`` is a class
#: level expression accessor, so sync and async models are both usable without
#: a live connection; the mapped models that declare ``FieldProxy`` are the
#: async twins already present in ``user_models.py``.
EXPRESSION_MODELS = (
    TypedUser,
    AsyncTypedUser,
    ComplexRow,
    AsyncComplexRow,
    ComplexRowAnnotated,
    AsyncComplexRowAnnotated,
    AsyncMappedUser,
)

_MISSING = object()


@pytest.fixture(scope="session")
def expression_backend(backend_scenario):
    """A backend instance that was constructed but never connected.

    Construction alone supplies ``.dialect`` (the column-class table is a
    static answer), so this avoids the database the other ``basic`` groups own.
    """
    config = backend_scenario.make_config("test_basic_expressions")
    return backend_scenario.backend_class(connection_config=config)


@pytest.fixture(scope="session")
def dialect(expression_backend):
    """The dialect the expressions render against, without opening a database.

    A backend that cannot answer column classes from an unadapted dialect is
    skipped by name rather than connected behind the suite's back (section 9).
    """
    found = getattr(expression_backend, "dialect", None)
    if found is None or not callable(getattr(found, "suggested_column_types", None)):
        pytest.skip(
            "{} exposes no dialect that answers column classes without an "
            "adapted backend; this directory owns no database".format(
                type(expression_backend).__name__
            )
        )
    return found


@pytest.fixture
def expression_models(expression_backend):
    """Bind the borrowed models to the unconnected backend, then restore them.

    ``FieldAccessor`` reads ``Model.backend().__dict__``'s backend only for its
    dialect; setting ``__backend__`` directly is exactly what ``configure()``
    does minus the connection and introspection this directory must avoid.
    """
    previous = {}
    for model in EXPRESSION_MODELS:
        previous[model] = model.__dict__.get("__backend__", _MISSING)
        model.__backend__ = expression_backend
    try:
        yield EXPRESSION_MODELS
    finally:
        for model, old in previous.items():
            if old is _MISSING:
                # Pydantic exposes a read-only class __dict__, so remove the
                # attribute we added rather than mutating that mapping.
                delattr(model, "__backend__")
            else:
                model.__backend__ = old
