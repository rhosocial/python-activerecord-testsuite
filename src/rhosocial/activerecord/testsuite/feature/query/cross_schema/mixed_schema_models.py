# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/mixed_schema_models.py
"""Fixture subclasses relocated into a non-default schema.

The table DDL is intentionally identical to the base fixtures: providers
provision the same ``orders`` shape in both the default namespace and
``SCHEMA_A``, so only ``__schema_name__`` differs between ``Order`` and
``MixedSchemaOrder``. Overriding the ``schema_name()`` classmethod would be
equivalent; subclassing with the attribute keeps the intent declarative.
"""

from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncOrder
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import Order
from rhosocial.activerecord.testsuite.feature.query.fixtures.schema_models import SCHEMA_A


class MixedSchemaOrder(Order):
    """Base ``orders`` fixture living in a non-default schema."""

    __schema_name__ = SCHEMA_A


class AsyncMixedSchemaOrder(AsyncOrder):
    """Async variant of ``MixedSchemaOrder``."""

    __schema_name__ = SCHEMA_A
