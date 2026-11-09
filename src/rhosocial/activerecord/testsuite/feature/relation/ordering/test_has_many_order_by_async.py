# src/rhosocial/activerecord/testsuite/feature/relation/ordering/test_has_many_order_by_async.py
"""
Integration tests for AsyncHasMany(order_by=...).

Mirrors the synchronous suite method-for-method, using the async
provider-backed User/Post/Comment models and test-local subclasses so the
provider interface stays unchanged.
"""

from typing import ClassVar

import pytest

from rhosocial.activerecord.relation import AsyncHasMany


def make_ordering_subclass(base_class, relation_name, related_class, foreign_key, inverse_of, order_by):
    """Build an async subclass of *base_class* with one AsyncHasMany(order_by=...) relation."""
    class_name = "{0}With{1}".format(
        base_class.__name__,
        relation_name.title().replace("_", ""),
    )
    return type(
        class_name,
        (base_class,),
        {
            "__module__": __name__,
            "__annotations__": {relation_name: ClassVar[AsyncHasMany[related_class]]},
            relation_name: AsyncHasMany(
                foreign_key=foreign_key,
                inverse_of=inverse_of,
                order_by=order_by,
            ),
        },
    )


def make_ordered_posts(user_class, post_class, relation_name="ordered_posts", order_by=(("title", "ASC"),)):
    """Build an async User subclass whose *relation_name* returns ordered posts."""
    return make_ordering_subclass(
        user_class,
        relation_name,
        post_class,
        foreign_key="user_id",
        inverse_of="user",
        order_by=order_by,
    )


def make_nested_classes(user_class, post_class, comment_class):
    """Build an ordered async User -> ordered Post -> ordered Comment chain."""
    OrderedPost = make_ordering_subclass(
        post_class,
        "ordered_comments",
        comment_class,
        foreign_key="post_id",
        inverse_of="post",
        order_by=("body", "ASC"),
    )
    OrderedUser = make_ordering_subclass(
        user_class,
        "ordered_posts",
        OrderedPost,
        foreign_key="user_id",
        inverse_of="user",
        order_by=("title", "ASC"),
    )
    return OrderedUser, OrderedPost


class TestAsyncHasManyOrderByIntegration:
    """Asynchronous integration tests for AsyncHasMany(order_by=...)."""

    async def test_direct_relation_access_is_ordered(self, async_user_post_comment_classes):
        """Direct access returns the declared order."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        user = OrderedUser(name="Ordered Direct")
        await user.save()
        for title in ("Charlie", "Alpha", "Bravo"):
            await post_class(title=title, body="Body", user_id=user.id).save()

        titles = [post.title for post in await user.ordered_posts()]
        assert titles == ["Alpha", "Bravo", "Charlie"], "Expected posts ordered by title ASC"

    async def test_relation_query_is_ordered(self, async_user_post_comment_classes):
        """{relation}_query() carries the default ordering before execution."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        user = OrderedUser(name="Ordered Query")
        await user.save()
        for title in ("Charlie", "Alpha", "Bravo"):
            await post_class(title=title, body="Body", user_id=user.id).save()

        titles = [post.title for post in await user.ordered_posts_query().all()]
        assert titles == ["Alpha", "Bravo", "Charlie"], "Expected relation query ordered by title ASC"

    async def test_chained_where_keeps_default_order(self, async_user_post_comment_classes):
        """A filter applied after the relation query does not disturb the order."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        user = OrderedUser(name="Ordered Filter")
        await user.save()
        for title, body in (("Charlie", "keep"), ("Alpha", "drop"), ("Bravo", "keep")):
            await post_class(title=title, body=body, user_id=user.id).save()

        query = user.ordered_posts_query().where(post_class.c.body == "keep")
        titles = [post.title for post in await query.all()]
        assert titles == ["Bravo", "Charlie"], "Expected filtered result to stay ordered"

    async def test_eager_loading_is_ordered(self, async_user_post_comment_classes):
        """Top-level eager loading applies the default order to each parent list."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        first = OrderedUser(name="Eager One")
        await first.save()
        second = OrderedUser(name="Eager Two")
        await second.save()
        for user, titles in ((first, ("C", "A")), (second, ("F", "D", "E"))):
            for title in titles:
                await post_class(title=title, body="Body", user_id=user.id).save()

        records = await OrderedUser.query().with_("ordered_posts").all()
        assert len(records) == 2
        for record in records:
            titles = [post.title for post in await record.ordered_posts()]
            assert titles == sorted(titles), "Expected every eager-loaded list to be ordered"

    async def test_eager_modifier_appends_secondary_order(self, async_user_post_comment_classes):
        """The default order comes first; a with_ modifier appends after it."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(
            user_class,
            post_class,
            relation_name="by_views",
            order_by=(("view_count", "DESC"),),
        )

        user = OrderedUser(name="Eager Modifier")
        await user.save()
        for title, view_count in (("a", 1), ("b", 3), ("c", 2)):
            await post_class(title=title, body="Body", user_id=user.id, view_count=view_count).save()

        records = await OrderedUser.query().with_(("by_views", lambda q: q.order_by("title"))).all()
        posts = await records[0].by_views()
        assert [post.view_count for post in posts] == [3, 2, 1], (
            "Expected the declared view_count DESC to remain the primary order"
        )

    async def test_nested_eager_loading_is_ordered(self, async_user_post_comment_classes):
        """Nested eager loading applies the default order at every level."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser, OrderedPost = make_nested_classes(user_class, post_class, comment_class)

        user = OrderedUser(name="Nested")
        await user.save()
        for post_title in ("Post B", "Post A"):
            post = OrderedPost(title=post_title, body="Body", user_id=user.id)
            await post.save()
            for body in ("Comment C", "Comment A", "Comment B"):
                await comment_class(body=body, post_id=post.id).save()

        records = await OrderedUser.query().with_("ordered_posts.ordered_comments").all()
        post_titles = [post.title for post in await records[0].ordered_posts()]
        assert post_titles == ["Post A", "Post B"], "Expected nested posts ordered by title"
        for post in await records[0].ordered_posts():
            bodies = [comment.body for comment in await post.ordered_comments()]
            assert bodies == ["Comment A", "Comment B", "Comment C"], "Expected nested comments ordered by body"

    async def test_cache_preserves_order_and_clear_refreshes(self, async_user_post_comment_classes):
        """The cached list is already ordered; clearing the cache refetches ordered data."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        user = OrderedUser(name="Cached")
        await user.save()
        for title in ("B", "A"):
            await post_class(title=title, body="Body", user_id=user.id).save()

        first = [post.title for post in await user.ordered_posts()]
        assert first == ["A", "B"]

        await post_class(title="C", body="Body", user_id=user.id).save()
        cached = [post.title for post in await user.ordered_posts()]
        assert cached == ["A", "B"], "Expected the second access to hit the relation cache"

        user.clear_relation_cache("ordered_posts")
        refreshed = [post.title for post in await user.ordered_posts()]
        assert refreshed == ["A", "B", "C"]

    async def test_empty_relation_returns_empty_list(self, async_user_post_comment_classes):
        """No child records still yields an empty list, not an ordering error."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        user = OrderedUser(name="Empty")
        await user.save()
        assert await user.ordered_posts() == []

    async def test_primary_key_tie_breaker_stabilizes_order(self, async_user_post_comment_classes):
        """Equal sort keys are resolved by the automatic primary-key tie-breaker."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(user_class, post_class)

        user = OrderedUser(name="Tie Break")
        await user.save()
        for _ in range(3):
            await post_class(title="Same Title", body="Body", user_id=user.id).save()

        posts = await user.ordered_posts()
        assert [post.title for post in posts] == ["Same Title"] * 3
        assert [post.id for post in posts] == sorted(post.id for post in posts), "Expected PK ASC tie-breaker"

    async def test_none_order_by_preserves_plain_has_many(self, async_user_post_comment_classes):
        """order_by=None keeps the old AsyncHasMany behaviour: no ordering, no tie-breakers."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        PlainUser = make_ordering_subclass(
            user_class,
            "plain_posts",
            post_class,
            foreign_key="user_id",
            inverse_of="user",
            order_by=None,
        )

        user = PlainUser(name="Plain")
        await user.save()
        for title in ("C", "A", "B"):
            await post_class(title=title, body="Body", user_id=user.id).save()

        sql, _params = user.plain_posts_query().to_sql()
        assert "ORDER BY" not in sql
        assert len(await user.plain_posts()) == 3

    async def test_unknown_field_fails_on_first_query_build(self, async_user_post_comment_classes):
        """An unknown field name raises ValueError when the query is built."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(
            user_class,
            post_class,
            relation_name="broken_posts",
            order_by=("does_not_exist",),
        )

        user = OrderedUser(name="Unknown Field")
        await user.save()
        with pytest.raises(ValueError, match="does_not_exist"):
            user.broken_posts_query()

    async def test_derived_field_fails_on_first_query_build(self, async_user_post_comment_classes):
        """Derived fields are not model fields and are rejected."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        OrderedUser = make_ordered_posts(
            user_class,
            post_class,
            relation_name="derived_posts",
            order_by=("title_length",),
        )

        user = OrderedUser(name="Derived Field")
        await user.save()
        with pytest.raises(ValueError, match="title_length"):
            user.derived_posts_query()
