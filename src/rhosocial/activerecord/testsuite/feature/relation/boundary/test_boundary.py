# src/rhosocial/activerecord/testsuite/feature/relation/boundary/test_boundary.py
"""
Backend-agnostic relation boundary tests.

Tests how relations behave when foreign keys are null, orphaned
(missing target), or no matching child records exist — for BelongsTo,
HasOne, and HasMany descriptors.

Uses provider-loaded fixture datasets (null_foreign_key, orphan_foreign_key,
owner_without_children, multiple_has_one_matches) so each backend injects
its own pre-built test data.
"""


class TestRelationBoundary:
    """Relation behavior for null, orphaned, and missing related data."""

    def test_belongs_to_returns_none_when_foreign_key_is_null(self, relation_boundary_context):
        """BelongsTo should return None when the foreign key is null."""
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "null_foreign_key")

        profile = profile_class.find_one(ids["profile_id"])

        assert profile is not None, "Expected the profile record to be found"
        assert profile.owner_id is None, "Expected profile.owner_id to be None"
        assert profile.owner() is None, "Expected profile.owner() to be None for null FK"

    def test_belongs_to_returns_none_for_missing_target(self, relation_boundary_context):
        """BelongsTo should return None when the target record is missing."""
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "orphan_foreign_key")

        post = post_class.find_one(ids["post_id"])

        assert post is not None, "Expected the post record to be found"
        assert post.owner_id == ids["missing_owner_id"], \
            "Expected post.owner_id to match the missing owner id"
        assert post.owner() is None, "Expected post.owner() to be None for orphan FK"
        assert post.owner() is None, "Expected post.owner() to remain None on re-access"

    def test_has_one_returns_none_when_no_match_exists(self, relation_boundary_context):
        """HasOne should return None when no matching related record exists."""
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = owner_class.find_one(ids["owner_id"])

        assert owner is not None, "Expected the owner record to be found"
        assert owner.profile() is None, "Expected owner.profile() to be None when no match"

    def test_has_many_returns_empty_list_when_no_match_exists(self, relation_boundary_context):
        """HasMany should return an empty list when no matching related records exist."""
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = owner_class.find_one(ids["owner_id"])

        assert owner is not None, "Expected the owner record to be found"
        assert owner.posts() == [], "Expected owner.posts() to be an empty list"

    def test_has_one_with_multiple_matches_returns_related_record(self, relation_boundary_context):
        """HasOne should return a related record when multiple matches exist."""
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "multiple_has_one_matches")

        owner = owner_class.find_one(ids["owner_id"])
        profile = owner.profile()

        assert owner is not None, "Expected the owner record to be found"
        assert profile is not None, "Expected a related profile to be returned"
        assert profile.owner_id == owner.id, "Expected profile.owner_id to match owner.id"
        assert profile.id in {ids["first_profile_id"], ids["second_profile_id"]}, \
            "Expected the profile id to be one of the multiple matches"
