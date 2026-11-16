# src/rhosocial/activerecord/testsuite/feature/basic/connection/fixtures.py
"""Backward-compatible view of the connection-pool models.

The declarations now live with the other basic fixtures in
``feature/basic/fixtures/connection_models.py``; this module keeps the names
the connection tests import.
"""

from rhosocial.activerecord.testsuite.feature.basic.fixtures.connection_models import (
    AsyncTestUser,
    TestUser,
)

__all__ = ["AsyncTestUser", "TestUser"]
