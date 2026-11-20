# src/rhosocial/activerecord/testsuite/feature/adapters/test_json_codec.py
"""JSON serialization contract: plain JSON, tagged codecs, and stability.

These checks are backend-agnostic: they exercise the core ``JSONAdapter`` and
``AdapterJSONCodec`` only.  The single database-backed case asserts that a
payload dict which happens to contain a ``__type__`` key stays a plain dict.
"""

from rhosocial.activerecord.backend.adapters.json_codec import (
    AdapterJSONCodec,
    register_type,
)
from rhosocial.activerecord.backend.adapters.vector import Vector
from rhosocial.activerecord.backend.type_adapter import JSONAdapter


class _Demo:
    json_type_tag = "testsuite_json_demo"

    def __init__(self, number: int):
        self.number = number

    def to_json_value(self):
        return {"number": self.number}

    @classmethod
    def from_json_value(cls, value):
        return cls(int(value["number"]))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Demo) and self.number == other.number


register_type("testsuite_json_demo", _Demo)


def test_plain_json_roundtrip_and_stability():
    adapter = JSONAdapter()
    value = {"a": 1, "b": [1, None, "x"], "nested": {"c": True}}
    text = adapter.to_database(value, str)
    assert adapter.from_database(text, dict) == value
    assert adapter.to_database(value, str) == text, "same value must serialize identically"


def test_tagged_codec_roundtrip_and_stability():
    codec = AdapterJSONCodec(tagged=True)
    adapter = JSONAdapter(default=codec.default, object_hook=codec.object_hook)
    value = {"demo": _Demo(7), "plain": [1, 2]}

    text = adapter.to_database(value, str)
    assert '"__type__": "testsuite_json_demo"' in text

    decoded = adapter.from_database(text, dict)
    assert decoded["demo"] == _Demo(7)
    assert decoded["plain"] == [1, 2]

    rewritten = adapter.to_database(decoded, str)
    assert rewritten == text, "tagged JSON must be byte-stable across rewrites"


def test_unknown_tag_is_preserved():
    codec = AdapterJSONCodec(tagged=True)
    adapter = JSONAdapter(default=codec.default, object_hook=codec.object_hook)
    text = '{"__type__": "unknown_tag", "value": 1}'
    assert adapter.from_database(text, dict) == {"__type__": "unknown_tag", "value": 1}


def test_untagged_mode_emits_no_marker():
    codec = AdapterJSONCodec(tagged=False)
    adapter = JSONAdapter(default=codec.default, object_hook=codec.object_hook)
    text = adapter.to_database({"demo": _Demo(1)}, str)
    assert "__type__" not in text


def test_driver_predecoded_value_passes_through():
    adapter = JSONAdapter()
    value = {"a": 1}
    assert adapter.from_database(value, dict) is value


def test_neutral_types_inside_tagged_json():
    codec = AdapterJSONCodec(tagged=True)
    adapter = JSONAdapter(default=codec.default, object_hook=codec.object_hook)
    value = {"vector": Vector([1.0, 2.0])}
    decoded = adapter.from_database(adapter.to_database(value, str), dict)
    assert decoded["vector"] == Vector([1.0, 2.0])


def test_database_payload_with_type_key_stays_plain(neutral_types):
    value = {"__type__": "not_a_type", "value": 1}
    instance = neutral_types(payload=value)
    instance.save()

    found = neutral_types.find_one(instance.id)
    assert found.payload == value, "a non-tagged dict must not be decoded"
