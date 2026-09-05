# src/rhosocial/activerecord/testsuite/feature/relation/boundary/test_boundary_async.py
"""
Async backend-agnostic relation boundary tests.
"""


class TestAsyncRelationBoundary:
    """Async relation behavior for null, orphaned, and missing related data."""

    async def test_belongs_to_returns_none_when_foreign_key_is_null(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "null_foreign_key")

        profile = await profile_class.find_one(ids["profile_id"])

        assert profile is not None, "Expected the profile record to be found"
        assert profile.owner_id is None, "Expected profile.owner_id to be None"
        assert await profile.owner() is None, "Expected profile.owner() to be None for null FK"

    async def test_belongs_to_returns_none_for_missing_target(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "orphan_foreign_key")

        post = await post_class.find_one(ids["post_id"])

        assert post is not None, "Expected the post record to be found"
        assert post.owner_id == ids["missing_owner_id"], \
            "Expected post.owner_id to match the missing owner id"
        assert await post.owner() is None, "Expected post.owner() to be None for orphan FK"
        assert await post.owner() is None, "Expected post.owner() to remain None on re-access"

    async def test_has_one_returns_none_when_no_match_exists(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = await owner_class.find_one(ids["owner_id"])

        assert owner is not None, "Expected the owner record to be found"
        assert await owner.profile() is None, "Expected owner.profile() to be None when no match"

    async def test_has_many_returns_empty_list_when_no_match_exists(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = await owner_class.find_one(ids["owner_id"])

        assert owner is not None, "Expected the owner record to be found"
        assert await owner.posts() == [], "Expected owner.posts() to be an empty list"

    async def test_has_one_with_multiple_matches_returns_related_record(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "multiple_has_one_matches")

        owner = await owner_class.find_one(ids["owner_id"])
        profile = await owner.profile()

        assert owner is not None, "Expected the owner record to be found"
        assert profile is not None, "Expected a related profile to be returned"
        assert profile.owner_id == owner.id, "Expected profile.owner_id to match owner.id"
        assert profile.id in {ids["first_profile_id"], ids["second_profile_id"]}, \
            "Expected the profile id to be one of the multiple matches"
