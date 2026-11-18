# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_field_generation_async.py
"""Async mirror of the field-generation contracts.

Generators are pure Python, so the async variant exercises the same runner on
``AsyncActiveRecord`` models. There is no I/O in generation itself; the mirror
exists to keep sync/async parity for the contract surface.
"""
from typing import Annotated, Optional

from rhosocial.activerecord.base import UseFieldGenerator
from rhosocial.activerecord.base.field_generation import apply_field_generators
from rhosocial.activerecord.field import DefaultSoftDeleteMixin, DefaultTimestampMixin
from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.types import WriteOperation


class AsyncGenerated(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "ts_async_field_generation"

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


async def test_async_generator_fills_and_filters_per_operation():
    row = AsyncGenerated()
    insert = apply_field_generators(AsyncGenerated, row, WriteOperation.INSERT, {"token": "", "touched": ""})
    assert insert == {"token": "new", "touched": "insert"}

    update = apply_field_generators(AsyncGenerated, row, WriteOperation.UPDATE, {"token": "stale", "touched": ""})
    assert update == {"touched": "update"}

    assert apply_field_generators(AsyncGenerated, row, WriteOperation.SOFT_DELETE, {}) == {"touched": "delete"}
    assert apply_field_generators(AsyncGenerated, row, WriteOperation.RESTORE, {}) == {"touched": "restore"}


async def test_async_mixins_expose_generators():
    class Doc(DefaultTimestampMixin, DefaultSoftDeleteMixin, AsyncActiveRecord):
        __primary_key__ = "id"
        id: Optional[int] = None

    generators = Doc.field_generators()
    assert generators["updated_at"].generator_for(WriteOperation.UPDATE) is not None
    assert generators["deleted_at"].generator_for(WriteOperation.SOFT_DELETE) is not None
