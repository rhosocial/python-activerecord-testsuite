# src/rhosocial/activerecord/testsuite/feature/query_integration/fixtures/definitions.py
"""L1 fixture definitions for the ``query_integration`` topic.

Only the four tables the combination tests share are declared here: ``users``,
``orders`` and ``order_items`` (the order group) plus ``nodes`` (the tree
group).  The definitions are self-contained in this topic -- nothing is
imported from another query topic's ``fixtures``.

A definition class holds the models of one table together with the DDL
expression instances they need.  It receives only a ``dialect`` and never a
backend, connection, database name or scenario: composing and executing the
environment belongs to the L2 fixtures in ``query_integration/conftest.py``.
"""
from rhosocial.activerecord.base.derivation import integer_auto_increment_parts  # noqa: E402

from rhosocial.activerecord.backend.expression import ColumnConstraint as Constraint
from rhosocial.activerecord.backend.expression import ColumnDefinition as Column
from rhosocial.activerecord.backend.expression import CreateTableStatement as CreateTable
from rhosocial.activerecord.backend.expression import DropTableStatement as DropTable
from rhosocial.activerecord.backend.expression import TableConstraint
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import ColumnDefaultConstraint as Default
from rhosocial.activerecord.backend.expression.statements import ColumnNotNullConstraint as NotNull
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.expression.statements import (
    TableUniqueConstraint as TableUnique,
)
from rhosocial.activerecord.backend.expression.types import BooleanType as Bool
from rhosocial.activerecord.backend.expression.types import DecimalType as Numeric
from rhosocial.activerecord.backend.expression.types import FloatType as Float
from rhosocial.activerecord.backend.expression.types import IntegerType as Int
from rhosocial.activerecord.backend.expression.types import TextType, TimestampType
from rhosocial.activerecord.backend.expression.types import VarCharType as VarChar

from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.async_cte_models import (
    AsyncNode,
)
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.cte_models import Node
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.models import (
    Order,
    OrderItem,
    User,
)

# --- Generic column type concepts (local to this group) --------------------

_SHORT_TEXT_LENGTH = 255
#: Portable non-empty text used as a column DEFAULT (the empty string is not
#: portable: some servers store it as NULL).
PLACEHOLDER_TEXT = "-"


def _require_data_type(dialect, concept: str) -> None:
    probe = getattr(dialect, "supports_data_types", None)
    if not callable(probe):
        return
    supported = probe() or {}
    if concept not in supported:
        import pytest

        pytest.skip(
            f"{getattr(dialect, 'name', 'this dialect')} does not support "
            f"the generic data type {concept!r}"
        )


def short_text(dialect):
    """Comparable text for identity-like columns (a bounded VARCHAR)."""
    _require_data_type(dialect, "varchar")
    return VarChar(dialect, _SHORT_TEXT_LENGTH)


def long_text(dialect):
    """Unbounded text payload; never compared or sorted."""
    return TextType(dialect)


def timestamp_type(dialect):
    """Timestamp with microsecond resolution where the server declares it."""
    probe = getattr(dialect, "supports_microsecond_timestamp", None)
    keeps_microseconds = bool(probe()) if callable(probe) else bool(probe)
    return TimestampType(dialect, precision=6 if keeps_microseconds else None)


def supports_drop_if_exists(dialect) -> bool:
    """Whether the dialect can spell ``DROP TABLE IF EXISTS``."""
    probe = getattr(dialect, "supports_if_exists_table", None)
    return True if probe is None else bool(probe())


class Definition:
    """Base class for this topic's table definitions."""

    model = None
    async_model = None
    table_name = ""

    def __init__(self, dialect, table_name=None):
        self.dialect = dialect
        self.name = table_name or type(self).table_name
        self.create_table = CreateTable(
            dialect,
            table=Table(dialect, self.name),
            columns=self.columns(),
            table_constraints=self.table_constraints(),
        )
        self.drop_table = DropTable(
            dialect,
            table=Table(dialect, self.name),
            if_exists=supports_drop_if_exists(dialect),
        )

    def columns(self):
        raise NotImplementedError

    def table_constraints(self):
        return []

    def column(self, name, sql_type, constraints=None):
        return Column(self.dialect, name, sql_type, constraints=constraints or [])

    def auto_pk(self, name="id"):
        data_type, attributes = integer_auto_increment_parts(self.dialect, Int(self.dialect))
        return Column(
            self.dialect,
            name,
            data_type,
            constraints=[Constraint(self.dialect, branch=PrimaryKey(self.dialect))],
            attributes=attributes,
        )

    def text(self, name):
        return self.column(name, short_text(self.dialect))

    def longtext(self, name):
        return self.column(name, long_text(self.dialect))

    def timestamp(self, name):
        return self.column(name, timestamp_type(self.dialect))

    def required_text(self, name):
        """Text column with the portable non-empty fixture default and NOT NULL."""
        return self.column(
            name,
            VarChar(self.dialect, 255),
            [
                Constraint(
                    self.dialect,
                    branch=Default(self.dialect, PLACEHOLDER_TEXT),
                ),
                Constraint(self.dialect, branch=NotNull(self.dialect)),
            ],
        )


class UsersDefinition(Definition):
    """The users table."""

    model = User
    async_model = AsyncUser
    table_name = "users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("username"),
            self.text("email"),
            self.column("age", Int(self.dialect)),
            self.column("balance", Float(self.dialect)),
            self.column("is_active", Bool(self.dialect)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class OrdersDefinition(Definition):
    """The orders table."""

    model = Order
    async_model = AsyncOrder
    table_name = "orders"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("user_id", Int(self.dialect)),
            self.text("order_number"),
            self.column("total_amount", Numeric(self.dialect, 12, 4)),
            self.text("status"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class OrderItemsDefinition(Definition):
    """The order_items table."""

    model = OrderItem
    async_model = AsyncOrderItem
    table_name = "order_items"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("order_id", Int(self.dialect)),
            self.column("product_id", Int(self.dialect)),
            self.required_text("product_name"),
            self.column("quantity", Int(self.dialect)),
            self.column("unit_price", Numeric(self.dialect, 12, 4)),
            self.column("subtotal", Numeric(self.dialect, 12, 4)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]

    def table_constraints(self):
        return [
            TableConstraint(
                self.dialect,
                branch=TableUnique(
                    self.dialect,
                    ["order_id", "product_id", "product_name"],
                ),
            )
        ]


class NodesDefinition(Definition):
    """The nodes table."""

    model = Node
    async_model = AsyncNode
    table_name = "nodes"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.column("parent_id", Int(self.dialect)),
            self.column("value", Numeric(self.dialect, 12, 4)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


__all__ = [
    "Definition",
    "NodesDefinition",
    "OrderItemsDefinition",
    "OrdersDefinition",
    "UsersDefinition",
]
