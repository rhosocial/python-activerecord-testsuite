# src/rhosocial/activerecord/testsuite/feature/ddl/test_ddl_source_contract.py

from typing import ClassVar, Optional

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

import pytest

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression.statements import (
    ColumnConstraintType,
    CreateIndexExpression,
    CreateTableExpression,
    CreateTableOptions,
    DropIndexExpression,
    DropTableExpression,
    IndexDefinition,
    PartitionStrategy,
    StorageOptionsExpression,
    TableConstraint,
    TableConstraintType,
)
from rhosocial.activerecord.backend.expression.statements.ddl_partition import PartitionClause
from rhosocial.activerecord.backend.expression.types import JsonType, TextType
from rhosocial.activerecord.base import (
    CharacterSetAttribute,
    CollationAttribute,
    ColumnOptions,
    DDLAnnotation,
    DDLAnnotationHandler,
    DDLSource,
    DerivedField,
    UseColumn,
    UseColumnAttributes,
    UseComment,
    UseConstraint,
    UseGeneratedColumn,
    UseIndex,
    UseSqlType,
)
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class BackendOptionAnnotation(DDLAnnotation):
    def __init__(self, option):
        self.option = option


class BackendOptionHandler(DDLAnnotationHandler):
    annotation_types = (BackendOptionAnnotation,)

    @classmethod
    def apply(cls, new_class, field_name, annotation, metadata):
        metadata.add_column_options(annotation.option)


class BackendOption(ColumnOptions):
    pass


BACKEND_OPTION = BackendOption()
SQL_TYPE = UseSqlType(JsonType(), JsonType(), TextType())
PAYLOAD_TYPE = UseSqlType(JsonType(), TextType())
DEFAULT_CONSTRAINT = UseConstraint(ColumnConstraintType.DEFAULT, default_value=7)
UNIQUE_CONSTRAINT = UseConstraint(ColumnConstraintType.UNIQUE, name="uq_payload")
FIRST_INDEX = UseIndex(
    "idx_payload",
    unique=True,
    type="BTREE",
    include_columns=["record_id"],
    if_not_exists=True,
    tablespace="index_space",
    if_exists=True,
    concurrent=True,
)
SECOND_INDEX = UseIndex("idx_payload_secondary", type="BTREE")
FIRST_COMMENT = UseComment("first comment")
SECOND_COMMENT = UseComment("second comment")


def first_generated(dialect):
    return object()


def second_generated(dialect):
    return object()


FIRST_GENERATED = first_generated
SECOND_GENERATED = second_generated
FIRST_GENERATED_MARKER = UseGeneratedColumn(FIRST_GENERATED)
SECOND_GENERATED_MARKER = UseGeneratedColumn(SECOND_GENERATED)
FIRST_ATTRIBUTES = UseColumnAttributes(
    CollationAttribute(name="und:ci"),
    CollationAttribute(name="und:ci"),
)
SECOND_ATTRIBUTES = UseColumnAttributes(CharacterSetAttribute(name="UTF8"))
TABLE_CONSTRAINT = TableConstraint(
    None,
    TableConstraintType.UNIQUE,
    name="uq_record_status",
    columns=["record_id", "status"],
)
TABLE_INDEX = IndexDefinition(
    None,
    name="idx_table_record",
    columns=["record_id"],
    unique=True,
)
TABLE_OPTIONS = CreateTableOptions(None, or_replace=True)
STORAGE_OPTIONS = StorageOptionsExpression(None, {"fillfactor": 80})
TABLE_PARTITION = PartitionClause(
    None,
    PartitionStrategy.RANGE,
    [Column(None, "record_id")],
)
TABLE_INHERITS = ["parent_records"]
TABLE_TABLESPACE = "record_space"


class ContractDeclarations:
    __table_name__ = "ddl_contract_records"
    __schema_name__ = "app"
    __primary_key__ = "record_id"
    __table_constraints__ = [TABLE_CONSTRAINT]
    __table_indexes__ = [TABLE_INDEX]
    _feature_handlers = [DDLAnnotationHandler, BackendOptionHandler]

    record_id: Annotated[int, UseColumn("record_id")]
    status: Annotated[
        str,
        SQL_TYPE,
        DEFAULT_CONSTRAINT,
        UNIQUE_CONSTRAINT,
        FIRST_INDEX,
        SECOND_INDEX,
        FIRST_ATTRIBUTES,
        SECOND_ATTRIBUTES,
        FIRST_COMMENT,
        SECOND_COMMENT,
        FIRST_GENERATED_MARKER,
        SECOND_GENERATED_MARKER,
        BackendOptionAnnotation(BACKEND_OPTION),
    ]
    payload: Annotated[Optional[dict], PAYLOAD_TYPE] = None
    note: Optional[str] = None

    @classmethod
    def table_options(cls):
        return TABLE_OPTIONS

    @classmethod
    def table_storage_options(cls):
        return STORAGE_OPTIONS

    @classmethod
    def table_partition(cls):
        return TABLE_PARTITION

    @classmethod
    def table_inherits(cls):
        return TABLE_INHERITS

    @classmethod
    def table_tablespace(cls):
        return TABLE_TABLESPACE

    @classmethod
    def create_table_statement_classes(cls):
        return CreateTableExpression

    @classmethod
    def drop_table_statement_classes(cls):
        return DropTableExpression

    @classmethod
    def create_index_statement_classes(cls):
        return CreateIndexExpression

    @classmethod
    def drop_index_statement_classes(cls):
        return DropIndexExpression


class SyncContractModel(ContractDeclarations, ActiveRecord):
    pass


class AsyncContractModel(ContractDeclarations, AsyncActiveRecord):
    pass


class DerivedDeclarations:
    __table_name__ = "ddl_contract_derived"

    id: int
    value: int
    total: ClassVar[Annotated[int, DerivedField(lambda dialect: object())]]


class SyncDerivedModel(DerivedDeclarations, ActiveRecord):
    pass


class AsyncDerivedModel(DerivedDeclarations, AsyncActiveRecord):
    pass


COMPOSITE_PRIMARY_KEY = TableConstraint(
    None,
    TableConstraintType.PRIMARY_KEY,
    columns=["left_id", "right_id"],
)


class CompositeDeclarations:
    __table_name__ = "ddl_contract_composite"
    __primary_key__ = ("left_id", "right_id")
    __table_constraints__ = [COMPOSITE_PRIMARY_KEY]

    left_id: Annotated[int, UseColumn("left_id")]
    right_id: Annotated[int, UseColumn("right_id")]


class SyncCompositeModel(CompositeDeclarations, ActiveRecord):
    pass


class AsyncCompositeModel(CompositeDeclarations, AsyncActiveRecord):
    pass


MISMATCHED_PRIMARY_KEY = TableConstraint(
    None,
    TableConstraintType.PRIMARY_KEY,
    columns=["right_id", "left_id"],
)


class MismatchedCompositeDeclarations:
    __table_name__ = "ddl_contract_mismatched_composite"
    __primary_key__ = ("left_id", "right_id")
    __table_constraints__ = [MISMATCHED_PRIMARY_KEY]

    left_id: int
    right_id: int


class MismatchedCompositeModel(MismatchedCompositeDeclarations, ActiveRecord):
    pass


class NullablePrimaryKeyDeclarations:
    __table_name__ = "ddl_contract_nullable_primary_key"
    __primary_key__ = "id"

    id: Annotated[Optional[int], UseConstraint(ColumnConstraintType.NULL)] = None


class NullablePrimaryKeyModel(NullablePrimaryKeyDeclarations, ActiveRecord):
    pass


class NotNullPrimaryKeyDeclarations:
    __table_name__ = "ddl_contract_not_null_primary_key"
    __primary_key__ = "id"

    id: Annotated[int, UseConstraint(ColumnConstraintType.NOT_NULL)]


class NotNullPrimaryKeyModel(NotNullPrimaryKeyDeclarations, ActiveRecord):
    pass


class PlainModel(ActiveRecord):
    __table_name__ = "ddl_contract_plain"

    id: int
    note: Optional[str] = None


class AsyncPlainModel(AsyncActiveRecord):
    __table_name__ = "ddl_contract_plain_async"

    id: int
    note: Optional[str] = None


class UnhandledAnnotation(DDLAnnotation):
    pass


class UnhandledModel(ActiveRecord):
    __table_name__ = "ddl_contract_unhandled"

    id: int
    value: Annotated[str, UnhandledAnnotation()]


@pytest.mark.parametrize("model", [SyncContractModel, AsyncContractModel], ids=("sync", "async"))
def test_contract_source_collects_table_and_field_declarations(model):
    assert isinstance(model, DDLSource)
    assert model.table_name() == "ddl_contract_records"
    assert model.schema_name() == "app"
    assert model.primary_key_columns() == ("record_id",)
    assert model.is_composite_pk() is False
    assert model.ddl_field_names() == ("record_id", "status", "payload", "note")
    assert model.is_derived_field("status") is False
    assert model.field_python_type("payload") is dict
    assert model.field_is_optional("payload") is True
    assert model.field_python_type("status") is str
    assert model.field_is_optional("status") is False
    assert model.column_name("record_id") == "record_id"
    assert model.column_name("status") == "status"
    assert model.column_name("payload") == "payload"
    assert model.column_name("note") == "note"
    metadata = model.ddl_field_metadata("status")
    assert metadata.annotations[0] is SQL_TYPE
    assert metadata.annotations[1] is DEFAULT_CONSTRAINT
    assert metadata.annotations[2] is UNIQUE_CONSTRAINT
    assert metadata.annotations[3] is FIRST_INDEX
    assert metadata.annotations[4] is SECOND_INDEX
    assert metadata.annotations[5] is FIRST_ATTRIBUTES
    assert metadata.annotations[6] is SECOND_ATTRIBUTES
    assert metadata.annotations[7] is FIRST_COMMENT
    assert metadata.annotations[8] is SECOND_COMMENT
    assert metadata.annotations[9] is FIRST_GENERATED_MARKER
    assert metadata.annotations[10] is SECOND_GENERATED_MARKER
    assert isinstance(metadata.annotations[11], BackendOptionAnnotation)
    assert metadata.annotations[11].option is BACKEND_OPTION


def test_contract_field_collection_preserves_order_and_first_singular_marker():
    model = SyncContractModel
    sql_type = model.column_type("status")
    assert sql_type is SQL_TYPE
    assert len(sql_type.data_types) == 2
    assert isinstance(sql_type.data_types[0], JsonType)
    assert isinstance(sql_type.data_types[1], TextType)
    constraints = model.column_constraints("status")
    assert [item.constraint_type for item in constraints] == [
        ColumnConstraintType.DEFAULT,
        ColumnConstraintType.UNIQUE,
        ColumnConstraintType.NOT_NULL,
    ]
    assert constraints[0] is DEFAULT_CONSTRAINT.constraint
    assert constraints[1] is UNIQUE_CONSTRAINT.constraint
    assert model.column_attributes("status") == [
        FIRST_ATTRIBUTES.attributes[0],
        SECOND_ATTRIBUTES.attributes[0],
    ]
    assert model.column_comment("status") == FIRST_COMMENT.comment
    assert model.generated_column("status") is FIRST_GENERATED
    indexes = model.column_indexes("status")
    assert [index.name for index in indexes] == [FIRST_INDEX.name, SECOND_INDEX.name]
    assert all(index.columns == ["status"] for index in indexes)
    assert indexes[0].unique is True
    assert indexes[0].include_columns is FIRST_INDEX.include_columns
    assert indexes[0].if_exists is True
    assert indexes[0].concurrent is True
    assert model.column_options("status") is BACKEND_OPTION
    assert model.column_type("payload") is PAYLOAD_TYPE
    assert len(model.column_type("payload").data_types) == 2
    assert isinstance(model.column_type("payload").data_types[0], JsonType)
    assert isinstance(model.column_type("payload").data_types[1], TextType)
    assert model.column_type("note") is None


def test_contract_table_collection_preserves_overrides_and_copies_sequences():
    model = SyncContractModel
    assert model.table_options() is TABLE_OPTIONS
    assert model.table_storage_options() is STORAGE_OPTIONS
    assert model.table_partition() is TABLE_PARTITION
    assert model.table_inherits() is TABLE_INHERITS
    assert model.table_tablespace() == TABLE_TABLESPACE
    assert model.create_table_statement_classes() is CreateTableExpression
    assert model.drop_table_statement_classes() is DropTableExpression
    assert model.create_index_statement_classes() is CreateIndexExpression
    assert model.drop_index_statement_classes() is DropIndexExpression
    indexes = model.table_indexes()
    assert indexes is not model.__table_indexes__
    assert indexes[0] is TABLE_INDEX
    constraints = model.table_constraints()
    assert constraints[0] is TABLE_CONSTRAINT
    assert len(constraints) == 1


def test_contract_batch_interfaces_cover_all_model_fields():
    model = SyncContractModel
    assert list(model.columns_name()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_type()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_constraints()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_attributes()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_indexes()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_comment()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_generated()) == ["record_id", "status", "payload", "note"]
    assert list(model.columns_options()) == ["record_id", "status", "payload", "note"]
    fields = ["status", "record_id", "note"]
    for method_name in (
        "columns_name",
        "columns_type",
        "columns_constraints",
        "columns_attributes",
        "columns_indexes",
        "columns_comment",
        "columns_generated",
        "columns_options",
    ):
        assert list(getattr(model, method_name)(fields)) == fields
    assert model.columns_name(fields) == {
        "status": "status",
        "record_id": "record_id",
        "note": "note",
    }
    assert model.columns_options(fields)["status"] is BACKEND_OPTION


@pytest.mark.parametrize("model", [SyncDerivedModel, AsyncDerivedModel], ids=("sync", "async"))
def test_contract_ddl_field_names_excludes_derived_fields(model):
    assert model.ddl_field_names() == ("id", "value")
    assert model.is_derived_field("total") is True
    assert model.is_derived_field("value") is False
    assert model.columns_name() == {"id": "id", "value": "value"}


@pytest.mark.parametrize(
    "model", [SyncCompositeModel, AsyncCompositeModel], ids=("sync", "async")
)
def test_contract_composite_primary_key_does_not_duplicate_explicit_constraint(model):
    constraints = model.table_constraints()
    primary_keys = [
        constraint
        for constraint in constraints
        if constraint.constraint_type == TableConstraintType.PRIMARY_KEY
    ]
    assert len(primary_keys) == 1
    assert primary_keys[0].columns == ["left_id", "right_id"]


def test_contract_mismatched_composite_primary_key_fails_explicitly():
    with pytest.raises(ValueError, match="does not match __primary_key__"):
        MismatchedCompositeModel.table_constraints()


def test_contract_primary_key_nullability_overrides_follow_source_rules():
    nullable_types = [
        constraint.constraint_type
        for constraint in NullablePrimaryKeyModel.column_constraints("id")
    ]
    not_null_types = [
        constraint.constraint_type
        for constraint in NotNullPrimaryKeyModel.column_constraints("id")
    ]
    assert nullable_types == [
        ColumnConstraintType.PRIMARY_KEY,
        ColumnConstraintType.NOT_NULL,
    ]
    assert not_null_types == [
        ColumnConstraintType.NOT_NULL,
        ColumnConstraintType.PRIMARY_KEY,
    ]


@pytest.mark.parametrize("model", [PlainModel, AsyncPlainModel], ids=("sync", "async"))
def test_contract_defaults_are_empty_or_none(model):
    assert model.ddl_field_names() == ("id", "note")
    assert model.column_type("id") is None
    assert model.column_constraints("note") == []
    assert model.column_attributes("note") == []
    assert model.column_indexes("note") == []
    assert model.column_comment("note") is None
    assert model.generated_column("note") is None
    assert model.column_options("note") is None
    assert model.table_options() is None
    assert model.table_storage_options() is None
    assert model.table_partition() is None
    assert model.table_inherits() is None
    assert model.table_tablespace() is None
    assert model.create_table_statement_classes() is None
    assert model.drop_table_statement_classes() is None
    assert model.create_index_statement_classes() is None
    assert model.drop_index_statement_classes() is None
    assert model.table_indexes() == []
    assert model.table_constraints() == []


def test_contract_unknown_fields_and_unhandled_annotations_fail_explicitly():
    assert SyncContractModel.column_type("missing") is None
    assert SyncContractModel.column_constraints("missing") == []
    assert SyncContractModel.column_attributes("missing") == []
    assert SyncContractModel.column_indexes("missing") == []
    assert SyncContractModel.column_comment("missing") is None
    assert SyncContractModel.generated_column("missing") is None
    assert SyncContractModel.column_options("missing") is None
    with pytest.raises(KeyError):
        SyncContractModel.field_python_type("missing")
    with pytest.raises(TypeError, match="explicit handler"):
        UnhandledModel.ddl_field_names()
