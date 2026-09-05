# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_example_basic_fixtures_async.py
"""
Example test file to import and verify the newly introduced mapped models fixtures.
"""

from rhosocial.activerecord.model import AsyncActiveRecord


async def test_mapped_models_fixtures_load(
    async_mapped_models_fixtures # Only import this specific fixture
):
    """Verify the async_mapped_models_fixtures fixture loads and contains AsyncActiveRecord subclasses."""
    assert async_mapped_models_fixtures is not None, \
        "Expected async_mapped_models_fixtures to be provided"
    assert isinstance(async_mapped_models_fixtures, tuple), \
        "Expected the fixture to be a tuple"
    assert len(async_mapped_models_fixtures) == 3, \
        "Expected 3 mapped models (MappedUser, MappedPost, MappedComment)"

    # Assert that each element in the tuple is an ActiveRecord subclass
    for model in async_mapped_models_fixtures:
        assert issubclass(model, AsyncActiveRecord), \
            f"Expected {model!r} to be an AsyncActiveRecord subclass"

    # Optionally, check specific names or types if needed
    # MappedUser, MappedPost, MappedComment = async_mapped_models_fixtures
    # assert MappedUser.__name__ == "MappedUser"
    # assert MappedPost.__name__ == "MappedPost"
    # assert MappedComment.__name__ == "MappedComment"

