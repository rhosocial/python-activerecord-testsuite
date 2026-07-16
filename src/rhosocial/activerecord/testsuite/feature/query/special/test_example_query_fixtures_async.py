# src/rhosocial/activerecord/testsuite/feature/query/special/test_example_query_fixtures_async.py
"""
Example test file to import and verify the newly introduced mapped models fixtures
for the query feature.
"""

from rhosocial.activerecord.model import AsyncActiveRecord

async def test_mapped_models_fixtures_load_query_feature(
    async_mapped_models_fixtures # Only import this specific fixture
):
    """
    This test checks if the async_mapped_models_fixtures can be loaded successfully for the query feature.
    It asserts that the fixture is not None and that its elements are AsyncActiveRecord subclasses.
    """
    assert async_mapped_models_fixtures is not None
    assert isinstance(async_mapped_models_fixtures, tuple)
    assert len(async_mapped_models_fixtures) == 3 # MappedUser, MappedPost, MappedComment

    # Assert that each element in the tuple is an AsyncActiveRecord subclass
    for model in async_mapped_models_fixtures:
        assert issubclass(model, AsyncActiveRecord)

    # Optionally, check specific names or types if needed
    # MappedUser, MappedPost, MappedComment = async_mapped_models_fixtures
    # assert MappedUser.__name__ == "MappedUser"
    # assert MappedPost.__name__ == "MappedPost"
    # assert MappedComment.__name__ == "MappedComment"

