# src/rhosocial/activerecord/testsuite/feature/query/typed_column/conftest.py
"""Shared fixtures for the typed-column contracts.

The ``dialect`` fixture used to be written out in each contract file. Three
copies of the same body had accumulated, each with a slightly different
docstring, and the duplication was load-bearing in the wrong direction: the
reason the fixture reads ``__backend__`` instead of calling ``Model.backend()``
is subtle enough that it should be explained once, in one place, rather than
three times with three different amounts of detail.

The local definitions in the existing contract files are left alone — pytest
lets a module-level fixture shadow a conftest one, so nothing changes for them —
and new contract files get this one without repeating the reasoning.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/conftest.py
import pytest


@pytest.fixture
def dialect(json_user_fixture):
    """The dialect under test, taken from a provider-configured model.

    Read off ``__backend__`` rather than calling ``Model.backend()``: that
    resolves the *currently active* backend and raises "No backend configured"
    on a shard with no live connection, which is the situation here — every
    assertion is on an expression tree or on SQL from a dialect that was never
    connected. ``__backend__`` is the instance the provider configured and
    needs no connection.

    The model arrives as a direct argument rather than through
    ``request.getfixturevalue``, because that cannot be combined with
    ``@pytest.mark.parametrize``: a parametrised test has no fixture parameter
    to resolve, and pytest rejects the request.
    """
    return json_user_fixture.__backend__.dialect
