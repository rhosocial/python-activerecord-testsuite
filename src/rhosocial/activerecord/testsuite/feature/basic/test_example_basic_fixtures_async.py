# src/rhosocial/activerecord/testsuite/feature/basic/test_example_basic_fixtures_async.py
"""
Example test file to import and verify the newly introduced mapped models fixtures.
"""

from rhosocial.activerecord.model import AsyncActiveRecord


async def test_mapped_models_fixtures_load(
    async_mapped_models_fixtures # Only import this specific fixture
):
    """
    This test checks if the async_mapped_models_fixtures can be loaded successfully.
    It asserts that the fixture is not None and that its elements are ActiveRecord subclasses.
    """
    assert async_mapped_models_fixtures is not None
    assert isinstance(async_mapped_models_fixtures, tuple)
    assert len(async_mapped_models_fixtures) == 3 # MappedUser, MappedPost, MappedComment

    # Assert that each element in the tuple is an ActiveRecord subclass
    for model in async_mapped_models_fixtures:
        assert issubclass(model, AsyncActiveRecord)

    # Optionally, check specific names or types if needed
    # MappedUser, MappedPost, MappedComment = async_mapped_models_fixtures
    # assert MappedUser.__name__ == "MappedUser"
    # assert MappedPost.__name__ == "MappedPost"
    # assert MappedComment.__name__ == "MappedComment"

