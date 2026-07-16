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

        assert profile is not None
        assert profile.owner_id is None
        assert await profile.owner() is None

    async def test_belongs_to_returns_none_for_missing_target(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "orphan_foreign_key")

        post = await post_class.find_one(ids["post_id"])

        assert post is not None
        assert post.owner_id == ids["missing_owner_id"]
        assert await post.owner() is None
        assert await post.owner() is None

    async def test_has_one_returns_none_when_no_match_exists(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = await owner_class.find_one(ids["owner_id"])

        assert owner is not None
        assert await owner.profile() is None

    async def test_has_many_returns_empty_list_when_no_match_exists(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = await owner_class.find_one(ids["owner_id"])

        assert owner is not None
        assert await owner.posts() == []

    async def test_has_one_with_multiple_matches_returns_related_record(
        self,
        async_relation_boundary_context,
    ):
        provider, scenario, owner_class, profile_class, post_class = async_relation_boundary_context
        ids = await provider.load_relation_boundary_dataset(scenario, "multiple_has_one_matches")

        owner = await owner_class.find_one(ids["owner_id"])
        profile = await owner.profile()

        assert owner is not None
        assert profile is not None
        assert profile.owner_id == owner.id
        assert profile.id in {ids["first_profile_id"], ids["second_profile_id"]}
