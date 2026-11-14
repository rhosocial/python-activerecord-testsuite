# src/rhosocial/activerecord/testsuite/feature/adapters/test_neutral_types.py
"""Shared contract: neutral types format and round-trip through generic carriers.

Only generic column types are involved (see ``testsuite.core.fixture_types``).
The suite asserts three kinds of consistency:

* **S1** -- a Python value written and read back is the same value;
* **S2** -- writing the value read back produces the same stored text
  (the stored form is stable, not re-encoded on every rewrite);
* **S3** -- a value written as native SQL text is decoded through the adapter
  and re-written in canonical form.
"""
import json


from rhosocial.activerecord.backend.adapters.bitstring import BitString
from rhosocial.activerecord.backend.adapters.geometry import LineString, Point
from rhosocial.activerecord.backend.adapters.network import MacAddress
from rhosocial.activerecord.backend.adapters.range import Multirange, Range
from rhosocial.activerecord.backend.adapters.vector import Vector
from rhosocial.activerecord.backend.expression import Column
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType

DML = ExecutionOptions(stmt_type=StatementType.DML)


def _insert(model, row):
    """Insert one row through native SQL, rendering values as literals.

    Identifiers go through the expression system, so a column that is a
    reserved word on some server (``vector`` on MariaDB 11.8) is quoted by that
    server's own dialect.
    """
    dialect = model.backend().dialect
    table_sql = Table(dialect, model.table_name()).to_sql()[0]
    columns = ", ".join(Column(dialect, name).to_sql()[0] for name in row)
    values = ", ".join(
        str(value) if isinstance(value, int) else dialect.format_literal(value)
        for value in row.values()
    )
    model.backend().execute(
        f"INSERT INTO {table_sql} ({columns}) VALUES ({values})", (), options=DML
    )


def _raw(model, column, pk):
    """Read the stored column value without any adapter."""
    dialect = model.backend().dialect
    table_sql = Table(dialect, model.table_name()).to_sql()[0]
    column_sql = Column(dialect, column).to_sql()[0]
    row = model.backend().fetch_one(
        f"SELECT {column_sql} FROM {table_sql} WHERE id = {int(pk)}", ()
    )
    return row[column]


def test_geometry_roundtrip(neutral_types):
    value = LineString([(0.0, 0.0), (1.0, 2.0)])
    instance = neutral_types(shape=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.shape == value, "neutral geometry must round-trip"
    assert found.shape.to_wkt() == value.to_wkt(), "WKT must be preserved"

    raw_before = _raw(neutral_types, "shape", instance.id)
    assert raw_before == value.to_wkt(), "the stored form is the neutral WKT text"

    found.shape = value
    found.save()
    assert _raw(neutral_types, "shape", instance.id) == raw_before, "the stored form must be stable"

    raw_id = 9001
    _insert(neutral_types, {"id": raw_id, "shape": "POINT(3 4)"})
    foreign = neutral_types.find_one(raw_id)
    assert foreign.shape == Point(3.0, 4.0), "foreign WKT must decode through the adapter"
    foreign.shape = Point(3.0, 4.0)
    foreign.save()
    assert _raw(neutral_types, "shape", raw_id) == Point(3.0, 4.0).to_wkt(), "re-written WKT must be canonical"


def test_vector_roundtrip(neutral_types):
    value = Vector([1.0, 2.5, -3.0])
    instance = neutral_types(vector=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.vector == value, "neutral vector must round-trip"
    assert json.loads(_raw(neutral_types, "vector", instance.id)) == [1.0, 2.5, -3.0]


def test_bitstring_roundtrip(neutral_types):
    value = BitString(data=b"\x28", bit_length=5)
    instance = neutral_types(flags=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.flags == value, "bit string must round-trip, including its length"
    assert found.flags.bit_length == 5
    assert _raw(neutral_types, "flags", instance.id) == "00101"

    raw_id = 9002
    _insert(neutral_types, {"id": raw_id, "flags": "1011"})
    foreign = neutral_types.find_one(raw_id)
    assert foreign.flags == BitString.from_bits("1011")


def test_range_roundtrip(neutral_types):
    # Range bound normalisation is backend-specific (a server may canonicalise
    # unbounded or exclusive endpoints), so the shared contract pins only the
    # canonical half-open form.  Each backend's own tests cover the variants.
    value = Range(1, 5, "[)")
    instance = neutral_types(window=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.window == value, "range must round-trip"


def test_multirange_roundtrip(neutral_types):
    value = Multirange([Range(1, 3, "[)"), Range(5, 7, "[)")])
    instance = neutral_types(windows=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.windows == value, "multirange must round-trip"

    shuffled = Multirange([Range(5, 7, "[)"), Range(1, 3, "[)")])
    other = neutral_types(windows=shuffled)
    other.save()
    assert neutral_types.find_one(other.id).windows == value, "multirange must canonicalise order"


def test_macaddress_roundtrip(neutral_types):
    value = MacAddress(bytes.fromhex("aabbccddeeff"))
    instance = neutral_types(address=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.address == value, "MAC address must round-trip"
    assert _raw(neutral_types, "address", instance.id) == "aa:bb:cc:dd:ee:ff"

    raw_id = 9003
    _insert(neutral_types, {"id": raw_id, "address": "AA:BB:CC:DD:EE:FF"})
    foreign = neutral_types.find_one(raw_id)
    assert foreign.address == value, "foreign MAC text must decode"
    foreign.address = value
    foreign.save()
    assert _raw(neutral_types, "address", raw_id) == "aa:bb:cc:dd:ee:ff", "rewritten MAC must be canonical"


def test_json_payload_roundtrip(neutral_types):
    value = {"a": 1, "b": [1, None, "x"], "unicode": "\u6d4b\u8bd5"}
    instance = neutral_types(payload=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.payload == value, "JSON payload must round-trip"

    raw_before = _raw(neutral_types, "payload", instance.id)
    assert json.loads(raw_before) == value
    found.payload = value
    found.save()
    assert _raw(neutral_types, "payload", instance.id) == raw_before, "JSON text must be stable"

    raw_id = 9004
    _insert(neutral_types, {"id": raw_id, "payload": '{"k": "v"}'})
    foreign = neutral_types.find_one(raw_id)
    assert foreign.payload == {"k": "v"}
    foreign.save()
    assert json.loads(_raw(neutral_types, "payload", raw_id)) == {"k": "v"}


def test_list_field_roundtrip(neutral_types):
    value = ["alpha", "beta"]
    instance = neutral_types(tags=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.tags == value, "list field must round-trip"


def test_empty_list_roundtrip(neutral_types):
    """The generic list field round-trips an empty list.

    ``NULL`` vs empty is a backend-specific distinction (a server may not
    allow a nullable array at all), so the shared contract only asserts the
    empty-list value itself.
    """
    instance = neutral_types(tags=[])
    instance.save()
    assert neutral_types.find_one(instance.id).tags == []


def test_null_values(neutral_types):
    instance = neutral_types()
    instance.save()
    found = neutral_types.find_one(instance.id)
    for field in ("shape", "point", "vector", "flags", "window", "windows", "address", "payload"):
        assert getattr(found, field) is None, f"{field} stays NULL"
