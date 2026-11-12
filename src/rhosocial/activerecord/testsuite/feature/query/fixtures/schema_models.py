# src/rhosocial/activerecord/testsuite/feature/query/fixtures/schema_models.py
"""Models bound to explicit, NON-default schema namespaces.

Used by the cross-schema query tests. The schema names are constants shared
with backend providers: the provider provisions ``SCHEMA_A`` / ``SCHEMA_B``
and the tables inside them, then returns these configured model classes.

Only backends whose dialect declares ``supports_schema()`` will run these
tests; everyone else skips via ``@requires_protocol``.
"""

from typing import ClassVar, Optional

from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

# Non-default schema namespaces provisioned by supporting backends.
SCHEMA_A = "ar_crm"    # customers live here
SCHEMA_B = "ar_shop"   # orders live here


class SchemaCustomer(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "customers"

    @classmethod
    def schema_name(cls):
        return SCHEMA_A

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str


class SchemaOrder(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "orders"

    @classmethod
    def schema_name(cls):
        return SCHEMA_B

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    customer_id: int
    amount: int


class AsyncSchemaCustomer(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "customers"

    @classmethod
    def schema_name(cls):
        return SCHEMA_A

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str


class AsyncSchemaOrder(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "orders"

    @classmethod
    def schema_name(cls):
        return SCHEMA_B

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    customer_id: int
    amount: int
