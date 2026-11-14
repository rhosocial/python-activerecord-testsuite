# src/rhosocial/activerecord/testsuite/feature/adapters/test_neutral_types_async.py
"""Async mirror of the neutral-type contract (adapter symmetry check)."""
import json

from rhosocial.activerecord.backend.adapters.bitstring import BitString
from rhosocial.activerecord.backend.adapters.geometry import LineString
from rhosocial.activerecord.backend.adapters.vector import Vector
from rhosocial.activerecord.backend.expression import Column
from rhosocial.activerecord.backend.expression.objects import Table


async def test_geometry_roundtrip_async(async_neutral_types):
    value = LineString([(0.0, 0.0), (2.0, 3.0)])
    instance = async_neutral_types(shape=value)
    await instance.save()

    found = await async_neutral_types.find_one(instance.id)
    assert found.shape == value, "neutral geometry must round-trip asynchronously"


async def test_vector_roundtrip_async(async_neutral_types):
    value = Vector([4.0, 5.5])
    instance = async_neutral_types(vector=value)
    await instance.save()

    found = await async_neutral_types.find_one(instance.id)
    assert found.vector == value, "neutral vector must round-trip asynchronously"

    dialect = async_neutral_types.backend().dialect
    table_sql = Table(dialect, async_neutral_types.table_name()).to_sql()[0]
    column_sql = Column(dialect, "vector").to_sql()[0]
    row = await async_neutral_types.backend().fetch_one(
        f"SELECT {column_sql} FROM {table_sql} WHERE id = {int(instance.id)}", ()
    )
    assert json.loads(row["vector"]) == [4.0, 5.5]


async def test_bitstring_and_payload_async(async_neutral_types):
    flags = BitString(data=b"\x28", bit_length=5)
    payload = {"k": "v", "n": 2}
    instance = async_neutral_types(flags=flags, payload=payload)
    await instance.save()

    found = await async_neutral_types.find_one(instance.id)
    assert found.flags == flags, "bit string must round-trip asynchronously"
    assert found.payload == payload, "JSON payload must round-trip asynchronously"
