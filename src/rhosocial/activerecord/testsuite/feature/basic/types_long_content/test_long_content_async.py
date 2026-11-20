# src/rhosocial/activerecord/testsuite/feature/basic/types_long_content/test_long_content_async.py
"""Asynchronous twin of ``test_long_content.py``.

Only the database-backed assertions are repeated here; the capability-skip and
sync/async DDL-parity checks are DB-free and live in the synchronous file.
"""

from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_long_content_models import (
    DOCUMENT_VALUE,
    LONG_BYTES,
    LONG_TEXT,
    MARKUP_VALUE,
    AsyncLongRow,
)


class TestAsyncLongContent:
    """Asynchronous round-trip and capacity assertions."""

    async def test_long_values_round_trip(self, schema, async_long_row_class):
        """A value at each declared minimum survives an async write/read."""
        row = async_long_row_class(
            body=LONG_TEXT,
            raw=LONG_BYTES,
            document=DOCUMENT_VALUE,
            markup=MARKUP_VALUE,
        )
        assert await row.save() == 1
        assert row.id is not None

        found = await async_long_row_class.find_one(row.id)
        assert found is not None
        assert found.body == LONG_TEXT
        assert len(found.body) == 16000
        assert found.raw == LONG_BYTES
        assert len(found.raw) == 16000
        assert found.document == DOCUMENT_VALUE
        assert found.markup == MARKUP_VALUE

    async def test_length_is_a_minimum_not_a_width(self, schema, async_long_row_class):
        """The async model carries the same minimum-capacity declarations."""
        assert AsyncLongRow.column_data_type("body").data_type.length == 16000
        assert AsyncLongRow.column_data_type("raw").data_type.length == 16000

        row = async_long_row_class(
            body=LONG_TEXT + "X",
            raw=LONG_BYTES + b"\x00",
            document=DOCUMENT_VALUE,
            markup=MARKUP_VALUE,
        )
        assert await row.save() == 1
        found = await async_long_row_class.find_one(row.id)
        assert len(found.body) == 16001
        assert len(found.raw) == 16001
