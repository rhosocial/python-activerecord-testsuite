# src/rhosocial/activerecord/testsuite/feature/query/fixtures/definitions.py
"""L1 fixture definitions for the query topic.

A definition class holds the models of one table together with the DDL
expression instances they need.  It receives only a ``dialect`` and never a
backend, connection, database name or scenario: composing and executing the
environment belongs to the L2 fixtures.

The models are spread over several sibling modules, so they are imported here
rather than re-declared.  Expression names are imported under short aliases so
the definitions stay readable.
"""

from rhosocial.activerecord.backend.expression import (
    ColumnConstraint as Constraint,
    ColumnDefinition as Column,
    CreateTableStatement as CreateTable,
    DropTableStatement as DropTable,
    TableConstraint,
)
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnDefaultConstraint as Default,
    ColumnNotNullConstraint as NotNull,
    ColumnPrimaryKeyConstraint as PrimaryKey,
    TableUniqueConstraint as TableUnique,
)
from rhosocial.activerecord.backend.expression.types import (
    BooleanType as Bool,
    DecimalType as Numeric,
    FloatType as Float,
    IntegerType as Int,
    VarCharType as VarChar,
)
from rhosocial.activerecord.testsuite.core.fixture_types import (
    PLACEHOLDER_TEXT,
    long_text,
    short_text,
    supports_drop_if_exists,
    timestamp_type,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.annotated_adapter_models import (
    SearchableItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_annotated_adapter_models import (
    AsyncSearchableItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_blog_models import (
    AsyncComment,
    AsyncPost,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import (
    AsyncNode,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_extended_models import (
    AsyncExtendedOrder,
    AsyncExtendedOrderItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_json_models import (
    AsyncJsonUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncProfile,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node
from rhosocial.activerecord.testsuite.feature.query.fixtures.extended_models import (
    ExtendedOrder,
    ExtendedOrderItem,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import (
    Comment,
    JsonUser,
    Order,
    OrderItem,
    Post,
    Profile,
    User,
)


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
        return self.column(
            name,
            Int(self.dialect),
            [
                Constraint(
                    self.dialect,
                    branch=PrimaryKey(self.dialect, is_auto_increment=True),
                )
            ],
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


class JsonUsersDefinition(Definition):
    """The json_users table."""

    model = JsonUser
    async_model = AsyncJsonUser
    table_name = "json_users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("username"),
            self.text("email"),
            self.column("age", Int(self.dialect)),
            self.longtext("settings"),
            self.longtext("tags"),
            self.longtext("profile"),
            self.longtext("roles"),
            self.longtext("scores"),
            self.longtext("subscription"),
            self.longtext("preferences"),
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
    """The order_items table.

    A superset of the query order item and the basic composite-key item.
    """

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


class PostsDefinition(Definition):
    """The posts table."""

    model = Post
    async_model = AsyncPost
    table_name = "posts"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("user_id", Int(self.dialect)),
            self.text("title"),
            self.longtext("content"),
            self.text("status"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class CommentsDefinition(Definition):
    """The comments table."""

    model = Comment
    async_model = AsyncComment
    table_name = "comments"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("user_id", Int(self.dialect)),
            self.column("post_id", Int(self.dialect)),
            self.longtext("content"),
            self.column("is_hidden", Bool(self.dialect)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class ProfilesDefinition(Definition):
    """The profiles table."""

    model = Profile
    async_model = AsyncProfile
    table_name = "profiles"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("user_id", Int(self.dialect)),
            self.longtext("bio"),
            self.text("avatar_url"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
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


class ExtendedOrdersDefinition(Definition):
    """The extended_orders table."""

    model = ExtendedOrder
    async_model = AsyncExtendedOrder
    table_name = "extended_orders"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("user_id", Int(self.dialect)),
            self.text("order_number"),
            self.column("total_amount", Numeric(self.dialect, 12, 4)),
            self.text("status"),
            self.text("priority"),
            self.text("region"),
            self.text("category"),
            self.text("product"),
            self.text("department"),
            self.text("year"),
            self.text("quarter"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class ExtendedOrderItemsDefinition(Definition):
    """The extended_order_items table."""

    model = ExtendedOrderItem
    async_model = AsyncExtendedOrderItem
    table_name = "extended_order_items"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("order_id", Int(self.dialect)),
            self.required_text("product_name"),
            self.column("quantity", Int(self.dialect)),
            self.column("price", Numeric(self.dialect, 12, 4)),
            self.text("category"),
            self.text("region"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class SearchableItemsDefinition(Definition):
    """The searchable_items table."""

    model = SearchableItem
    async_model = AsyncSearchableItem
    table_name = "searchable_items"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.longtext("tags"),
        ]


__all__ = [
    "CommentsDefinition",
    "Definition",
    "ExtendedOrderItemsDefinition",
    "ExtendedOrdersDefinition",
    "JsonUsersDefinition",
    "NodesDefinition",
    "OrderItemsDefinition",
    "OrdersDefinition",
    "PostsDefinition",
    "ProfilesDefinition",
    "SearchableItemsDefinition",
    "UsersDefinition",
]
