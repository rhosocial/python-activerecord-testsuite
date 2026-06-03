# src/rhosocial/activerecord/testsuite/feature/relation/test_boundary.py
"""
Backend-agnostic relation boundary tests.
"""


class TestRelationBoundary:
    """Relation behavior for null, orphaned, and missing related data."""

    def test_belongs_to_returns_none_when_foreign_key_is_null(self, relation_boundary_context):
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "null_foreign_key")

        profile = profile_class.find_one(ids["profile_id"])

        assert profile is not None
        assert profile.owner_id is None
        assert profile.owner() is None

    def test_belongs_to_returns_none_for_missing_target(self, relation_boundary_context):
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "orphan_foreign_key")

        post = post_class.find_one(ids["post_id"])

        assert post is not None
        assert post.owner_id == ids["missing_owner_id"]
        assert post.owner() is None
        assert post.owner() is None

    def test_has_one_returns_none_when_no_match_exists(self, relation_boundary_context):
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = owner_class.find_one(ids["owner_id"])

        assert owner is not None
        assert owner.profile() is None

    def test_has_many_returns_empty_list_when_no_match_exists(self, relation_boundary_context):
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "owner_without_children")

        owner = owner_class.find_one(ids["owner_id"])

        assert owner is not None
        assert owner.posts() == []

    def test_has_one_with_multiple_matches_returns_related_record(self, relation_boundary_context):
        provider, scenario, owner_class, profile_class, post_class = relation_boundary_context
        ids = provider.load_relation_boundary_dataset(scenario, "multiple_has_one_matches")

        owner = owner_class.find_one(ids["owner_id"])
        profile = owner.profile()

        assert owner is not None
        assert profile is not None
        assert profile.owner_id == owner.id
        assert profile.id in {ids["first_profile_id"], ids["second_profile_id"]}
