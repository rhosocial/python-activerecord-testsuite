# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_example_basic_fixtures.py
"""
Example test file to import and verify the newly introduced mapped models fixtures.
"""

import pytest
from rhosocial.activerecord.model import ActiveRecord

def test_mapped_models_fixtures_load(
    mapped_models_fixtures # Only import this specific fixture
):
    """Verify the mapped_models_fixtures fixture loads and contains ActiveRecord subclasses."""
    assert mapped_models_fixtures is not None, "Expected mapped_models_fixtures to be provided"
    assert isinstance(mapped_models_fixtures, tuple), "Expected the fixture to be a tuple"
    assert len(mapped_models_fixtures) == 3, \
        "Expected 3 mapped models (MappedUser, MappedPost, MappedComment)"

    # Assert that each element in the tuple is an ActiveRecord subclass
    for model in mapped_models_fixtures:
        assert issubclass(model, ActiveRecord), \
            f"Expected {model!r} to be an ActiveRecord subclass"

    # Optionally, check specific names or types if needed
    # MappedUser, MappedPost, MappedComment = mapped_models_fixtures
    # assert MappedUser.__name__ == "MappedUser"
    # assert MappedPost.__name__ == "MappedPost"
    # assert MappedComment.__name__ == "MappedComment"

