# src/rhosocial/activerecord/testsuite/feature/query/test_example_query_fixtures.py
"""
Example test file to import and verify the newly introduced mapped models fixtures
for the query feature.
"""

import pytest
from rhosocial.activerecord.model import ActiveRecord

def test_mapped_models_fixtures_load_query_feature(
    mapped_models_fixtures # Only import this specific fixture
):
    """
    This test checks if the mapped_models_fixtures can be loaded successfully for the query feature.
    It asserts that the fixture is not None and that its elements are ActiveRecord subclasses.
    """
    assert mapped_models_fixtures is not None
    assert isinstance(mapped_models_fixtures, tuple)
    assert len(mapped_models_fixtures) == 3 # MappedUser, MappedPost, MappedComment

    # Assert that each element in the tuple is an ActiveRecord subclass
    for model in mapped_models_fixtures:
        assert issubclass(model, ActiveRecord)

    # Optionally, check specific names or types if needed
    # MappedUser, MappedPost, MappedComment = mapped_models_fixtures
    # assert MappedUser.__name__ == "MappedUser"
    # assert MappedPost.__name__ == "MappedPost"
    # assert MappedComment.__name__ == "MappedComment"

