# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_field_generation.py
"""Cross-backend contracts for ActiveRecord-side field generators (sync).

Field generators are a pure-Python ActiveRecord capability: they fill a field
with a value before a write and filter it out of write sets where no generator
is declared. They are backend-agnostic, so these contracts run unchanged on
every backend -- no database connection or dialect is required.
"""
try:  # Python 3.8 has no typing.Annotated
    from typing import Annotated, Optional
except ImportError:  # pragma: no cover - only on 3.8
    from typing_extensions import Annotated

    from typing import Optional

from rhosocial.activerecord.base import UseFieldGenerator
from rhosocial.activerecord.base.field_generation import apply_field_generators
from rhosocial.activerecord.field import (
    DefaultSoftDeleteMixin,
    DefaultTimestampMixin,
    UUIDMixin,
)
from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.types import WriteOperation


class Generated(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "ts_field_generation"

    __primary_key__ = "id"

    id: Optional[int] = None
    token: Annotated[str, UseFieldGenerator(before_insert=lambda self: "new")] = ""
    touched: Annotated[
        str,
        UseFieldGenerator(
            before_insert=lambda self: "insert",
            before_update=lambda self: "update",
            before_soft_delete=lambda self: "delete",
            before_restore=lambda self: "restore",
        ),
    ] = ""


def test_generator_annotation_declares_only_configured_operations():
    annotation = Generated.model_fields["token"].metadata[0]
    assert isinstance(annotation, UseFieldGenerator)
    assert annotation.operations() == (WriteOperation.INSERT,)
    assert annotation.generator_for(WriteOperation.UPDATE) is None


def test_apply_generator_fills_and_filters_per_operation():
    row = Generated()
    insert = apply_field_generators(Generated, row, WriteOperation.INSERT, {"id": None, "token": "", "touched": ""})
    assert insert["token"] == "new"
    assert insert["touched"] == "insert"

    update = apply_field_generators(Generated, row, WriteOperation.UPDATE, {"token": "stale", "touched": ""})
    assert "token" not in update  # filtered out on update
    assert update["touched"] == "update"

    soft_delete = apply_field_generators(Generated, row, WriteOperation.SOFT_DELETE, {})
    assert soft_delete == {"touched": "delete"}

    restore = apply_field_generators(Generated, row, WriteOperation.RESTORE, {})
    assert restore == {"touched": "restore"}


def test_mixins_expose_generators_for_their_fields():
    class Doc(DefaultTimestampMixin, DefaultSoftDeleteMixin, ActiveRecord):
        __primary_key__ = "id"
        id: Optional[int] = None

    generators = Doc.field_generators()
    assert "created_at" in generators
    assert "updated_at" in generators
    assert "deleted_at" in generators
    assert generators["created_at"].generator_for(WriteOperation.UPDATE) is None
    assert generators["updated_at"].generator_for(WriteOperation.UPDATE) is not None
    assert generators["deleted_at"].generator_for(WriteOperation.SOFT_DELETE) is not None
    assert generators["deleted_at"].generator_for(WriteOperation.RESTORE) is not None


def test_uuid_pk_generator_cancels_database_identity():
    class Key(UUIDMixin, ActiveRecord):
        pass

    assert Key.pk_auto_generated() is False
    assert "id" not in Key.identity_pk_fields()
