# src/rhosocial/activerecord/testsuite/feature/query/eager_loading/test_eager_loading_scenarios_async.py
"""Async: extended eager loading scenario tests.

Mirrors test_eager_loading_scenarios_sync.py exactly for sync/async parity.
"""
from decimal import Decimal


# ---------------------------------------------------------------------------
# Helper: async query-counting wrapper
# ---------------------------------------------------------------------------
class AsyncQueryCounter:
    """Counts SELECT queries (fetch_all / fetch_one) on an AsyncStorageBackend."""

    def __init__(self, model_or_backend):
        if hasattr(model_or_backend, "backend"):
            self._backend = model_or_backend.backend()
        else:
            self._backend = model_or_backend
        self.select_count = 0

    def install(self):
        orig_fetch_all = self._backend.fetch_all

        async def counting_fetch_all(*args, **kwargs):
            self.select_count += 1
            return await orig_fetch_all(*args, **kwargs)

        self._backend.fetch_all = counting_fetch_all
        orig_fetch_one = self._backend.fetch_one

        async def counting_fetch_one(*args, **kwargs):
            self.select_count += 1
            return await orig_fetch_one(*args, **kwargs)

        self._backend.fetch_one = counting_fetch_one
        return self


# ---------------------------------------------------------------------------
# 1. SQL query count verification
# ---------------------------------------------------------------------------
class TestAsyncQueryCount:
    """Async: verify N+1 prevention via query counters."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_has_many_count(self, async_combined_fixtures):
        """HasMany: with_('orders') → 2 queries regardless of N (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_hm', email='aqc_hm@example.com', age=25)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-HM-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()

        counter = self._install_counter(AsyncUser)
        results = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1, "Expected exactly one result"
        related = await results[0].orders()
        assert len(related) == 3, "Expected three related orders"
        assert counter.select_count == 2, f"Expected 2 async queries, got {counter.select_count}"

    async def test_belongs_to_count(self, async_combined_fixtures):
        """BelongsTo: with_('user') on N orders → 2 queries (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_bt', email='aqc_bt@example.com', age=25)
        await user.save()
        for i in range(4):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-BT-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()

        counter = self._install_counter(AsyncOrder)
        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.user_id == user.id).all()
        assert len(results) == 4, "Expected four results"
        for o in results:
            assert await o.user() is not None, "Expected the related user to be loaded"
        assert counter.select_count == 2, f"Expected 2 async queries, got {counter.select_count}"

    async def test_multiple_relations_count(self, async_combined_fixtures):
        """Multiple with_: with_('orders', 'posts') on 1 user → 3 queries (async)."""
        AsyncUser, AsyncOrder, _, AsyncPost, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_mr', email='aqc_mr@example.com', age=25)
        await user.save()
        for i in range(2):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-MR-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()
            p = AsyncPost(title=f'AQC-MR-{i}', content='x', user_id=user.id,
                          status='published')
            await p.save()

        counter = self._install_counter(AsyncUser)
        results = await AsyncUser.query().with_('orders', 'posts').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1, "Expected exactly one result"
        assert len(await results[0].orders()) == 2, "Expected two related orders"
        assert len(await results[0].posts()) == 2, "Expected two related posts"
        assert counter.select_count == 3, f"Expected 3 queries, got {counter.select_count}"

    async def test_without_eager_is_nplus1(self, async_combined_fixtures):
        """Baseline: without with_() causes N+1 (1 + N queries) (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_n1', email='aqc_n1@example.com', age=25)
        await user.save()
        for i in range(4):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-N1-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()

        counter = self._install_counter(AsyncOrder)
        results = await AsyncOrder.query().where(AsyncOrder.c.user_id == user.id).all()
        assert len(results) == 4, "Expected four results"
        for o in results:
            _ = await o.user()
        assert counter.select_count == 5, f"Expected 5 async queries (N+1), got {counter.select_count}"


# ---------------------------------------------------------------------------
# 2. Empty relation boundary
# ---------------------------------------------------------------------------
class TestAsyncEmptyRelation:
    """Async: parent exists, related table is empty."""

    async def test_has_many_empty(self, async_combined_fixtures):
        """Parent with no orders → .orders() returns [] (async)."""
        AsyncUser, _, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aempty_hm', email='aempty_hm@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        related = await result.orders()
        assert related == [], "Expected the related list to be empty"

    async def test_belongs_to_none(self, async_combined_fixtures):
        """Order with no matching user → .user() returns None (async).

        Note: Creates an orphaned FK reference by first saving a User,
        then an Order referencing it, then deleting the User. This requires
        the Provider's schema to either not have FK constraints or use
        ON DELETE CASCADE/SET NULL for this test to pass.
        """
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aorphan_ref', email='aorphan_ref@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AORPHAN-001', total_amount=Decimal('10'))
        await order.save()

        # Attempt to delete the User — may fail if FK enforcement is ON.
        try:
            await user.delete()
        except Exception:
            return

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None, "Expected the order to be loaded"
        related = await result.user()
        assert related is None, "Expected the related user to be None for an orphan FK"

    async def test_has_many_empty_list_after_eager(self, async_combined_fixtures):
        """HasMany: relation_name() returns [] when empty (async)."""
        AsyncUser, _, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aemplist', email='aemplist@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        orders = await result.orders()
        assert isinstance(orders, list), "Expected the related orders to be a list"
        assert len(orders) == 0, "Expected zero related orders"


# ---------------------------------------------------------------------------
# 3. all() empty result — with_() must not fire any batch query
# ---------------------------------------------------------------------------
class TestAsyncEmptyResultNoQuery:
    """Async: .all()/.one() empty → no batch queries."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_all_empty_no_batch(self, async_combined_fixtures):
        """No matching parent → all() returns [] and 1 query total (async)."""
        _, AsyncOrder, _, _, _ = async_combined_fixtures
        counter = self._install_counter(AsyncOrder)
        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == -1).all()
        assert results == [], "Expected an empty result list"
        assert counter.select_count == 1, f"Expected 1 async query, got {counter.select_count}"

    async def test_one_none_no_batch(self, async_combined_fixtures):
        """No matching parent → one() returns None and 1 query total (async)."""
        _, AsyncOrder, _, _, _ = async_combined_fixtures
        counter = self._install_counter(AsyncOrder)
        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == -1).one()
        assert result is None, "Expected the result to be None"
        assert counter.select_count == 1, f"Expected 1 async query, got {counter.select_count}"


# ---------------------------------------------------------------------------
# 4. HasOne batch loading
# ---------------------------------------------------------------------------
class TestAsyncHasOneEagerLoading:
    """Async: verify HasOne can be batch-loaded via with_()."""

    async def test_has_one_eager(self, async_profile_fixtures):
        """with_('profile') should preload HasOne relation (async)."""
        AsyncUser, AsyncProfile = async_profile_fixtures
        user = AsyncUser(username='aho_user', email='aho_user@example.com', age=25)
        await user.save()
        profile = AsyncProfile(user_id=user.id, bio="Test bio", avatar_url="http://example.com/av.jpg")
        await profile.save()

        result = await AsyncUser.query().with_('profile').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        related = await result.profile()
        assert related is not None, "Expected the related profile to be loaded"
        assert related.bio == "Test bio", "Expected the related profile bio to match"

    async def test_has_one_count(self, async_profile_fixtures):
        """with_('profile') → 2 queries regardless of N (async)."""
        AsyncUser, AsyncProfile = async_profile_fixtures
        counter = AsyncQueryCounter(AsyncUser).install()
        user = AsyncUser(username='aho_count', email='aho_count@example.com', age=25)
        await user.save()
        await AsyncProfile(user_id=user.id, bio="Count test").save()

        results = await AsyncUser.query().with_('profile').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1, "Expected exactly one result"
        p = await results[0].profile()
        assert p is not None, "Expected the related profile to be loaded"
        assert counter.select_count == 2, f"Expected 2 async queries, got {counter.select_count}"

    async def test_has_one_empty(self, async_profile_fixtures):
        """User with no profile → .profile() returns None (async)."""
        AsyncUser, _ = async_profile_fixtures
        user = AsyncUser(username='aho_empty', email='aho_empty@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('profile').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        profile = await result.profile()
        assert profile is None, "Expected the related profile to be None"


# ---------------------------------------------------------------------------
# 5. HasMany empty → []  (covered in TestAsyncEmptyRelation above)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 6. with_() vs lazy loading mutual exclusion
# ---------------------------------------------------------------------------
class TestAsyncEagerVsLazyParity:
    """Async: eager and lazy produce identical results."""

    async def test_eager_vs_lazy_has_many(self, async_combined_fixtures):
        """Eager and lazy return identical data for HasMany (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aparity', email='aparity@example.com', age=30)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'APARITY-{i:03d}',
                           total_amount=Decimal(f'{(i + 1) * 10}'))
            await o.save()

        eager = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        eager_orders = sorted(await eager.orders(), key=lambda o: o.id)

        lazy_user = await AsyncUser.find_one(user.id)
        lazy_orders = sorted(await lazy_user.orders(), key=lambda o: o.id)

        assert len(eager_orders) == len(lazy_orders), \
            "Expected eager and lazy to return the same number of orders"
        for eo, lo in zip(eager_orders, lazy_orders):
            assert eo.order_number == lo.order_number, \
                "Expected eager and lazy order numbers to match"
            assert eo.total_amount == lo.total_amount, \
                "Expected eager and lazy order totals to match"

    async def test_eager_vs_lazy_belongs_to(self, async_combined_fixtures):
        """Eager and lazy return identical User for BelongsTo (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aparity_bt', email='aparity_bt@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='APARITY-BT-001', total_amount=Decimal('50'))
        await order.save()

        eager = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        eager_user = await eager.user()

        lazy_order = await AsyncOrder.find_one(order.id)
        lazy_user = await lazy_order.user()

        assert eager_user.id == lazy_user.id, "Expected eager and lazy user ids to match"
        assert eager_user.username == lazy_user.username, \
            "Expected eager and lazy usernames to match"


# ---------------------------------------------------------------------------
# 7. Mixed with_() + lazy — part cached, part lazy-loaded
# ---------------------------------------------------------------------------
class TestAsyncMixedEagerLazy:
    """Async: some relations eager, some lazy."""

    async def test_mixed_relations(self, async_combined_fixtures):
        """with_('user') eager, items lazy (async)."""
        AsyncUser, AsyncOrder, AsyncOrderItem, _, _ = async_combined_fixtures
        user = AsyncUser(username='amixed', email='amixed@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AMIXED-001', total_amount=Decimal('50'))
        await order.save()
        item = AsyncOrderItem(order_id=order.id, product_name='AM-Item', quantity=1,
                              unit_price=Decimal('25'), subtotal=Decimal('25'))
        await item.save()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None, "Expected the order to be loaded"

        eager_user = await result.user()
        assert eager_user is not None, "Expected the eagerly loaded user to be present"
        assert eager_user.username == 'amixed', "Expected the eagerly loaded username to match"

        lazy_items = await result.items()
        assert len(lazy_items) == 1, "Expected one lazily loaded item"
        assert lazy_items[0].product_name == 'AM-Item', "Expected the item product_name to match"

    async def test_mixed_eager_then_lazy_same_relation(self, async_combined_fixtures):
        """First access via eager, second via lazy — both work (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='amix2', email='amix2@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AMIXED-002', total_amount=Decimal('50'))
        await order.save()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None, "Expected the order to be loaded"

        u1 = await result.user()
        assert u1 is not None, "Expected the first access to return a user"
        u2 = await result.user()
        assert u2 is not None, "Expected the cached access to return a user"
        assert u2.id == u1.id, "Expected both accesses to return the same user"


# ---------------------------------------------------------------------------
# 8. Post.comments (HasMany) and Comment.user/post (BelongsTo) eager loading
# ---------------------------------------------------------------------------
class TestAsyncBlogEagerLoading:
    """Async: verify Post.comments HasMany and Comment BelongsTo eager loading."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_post_comments_eager(self, async_blog_fixtures):
        """with_('comments') on Post should preload HasMany comments (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='abe_user', email='abe_user@example.com', age=25)
        await user.save()
        post = AsyncPost(title='BE Post', content='Blog content', user_id=user.id, status='published')
        await post.save()
        for i in range(3):
            c = AsyncComment(content=f'Comment {i}', user_id=user.id, post_id=post.id, is_hidden=False)
            await c.save()

        result = await AsyncPost.query().with_('comments').where(AsyncPost.c.id == post.id).one()
        assert result is not None, "Expected the post to be loaded"
        comments = await result.comments()
        assert len(comments) == 3, "Expected three related comments"
        for c in comments:
            assert c.post_id == post.id, "Expected each comment's post_id to match"

    async def test_post_comments_count(self, async_blog_fixtures):
        """with_('comments') → 2 queries regardless of N (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='abe_count', email='abe_count@example.com', age=25)
        await user.save()
        for pi in range(3):
            post = AsyncPost(title=f'BE Post {pi}', content='x', user_id=user.id, status='published')
            await post.save()
            for ci in range(2):
                c = AsyncComment(content=f'C {pi}-{ci}', user_id=user.id, post_id=post.id, is_hidden=False)
                await c.save()

        counter = self._install_counter(AsyncPost)
        results = await AsyncPost.query().with_('comments').all()
        assert len(results) == 3, "Expected three posts"
        for p in results:
            assert len(await p.comments()) == 2, "Expected two comments per post"
        assert counter.select_count == 2, f"Expected 2 queries, got {counter.select_count}"

    async def test_comment_user_eager(self, async_blog_fixtures):
        """with_('author') on Comment should preload BelongsTo author (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='acu_user', email='acu_user@example.com', age=25)
        await user.save()
        post = AsyncPost(title='CU Post', content='x', user_id=user.id, status='published')
        await post.save()
        comment = AsyncComment(content='Hello', user_id=user.id, post_id=post.id, is_hidden=False)
        await comment.save()

        result = await AsyncComment.query().with_('author').where(AsyncComment.c.id == comment.id).one()
        assert result is not None, "Expected the comment to be loaded"
        u = await result.author()
        assert u is not None, "Expected the related author to be loaded"
        assert u.username == 'acu_user', "Expected the related author username to match"

    async def test_comment_post_eager(self, async_blog_fixtures):
        """with_('post') on Comment should preload BelongsTo post (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='acp_user', email='acp_user@example.com', age=25)
        await user.save()
        post = AsyncPost(title='CP Post', content='x', user_id=user.id, status='published')
        await post.save()
        comment = AsyncComment(content='Hello', user_id=user.id, post_id=post.id, is_hidden=False)
        await comment.save()

        result = await AsyncComment.query().with_('post').where(AsyncComment.c.id == comment.id).one()
        assert result is not None, "Expected the comment to be loaded"
        p = await result.post()
        assert p is not None, "Expected the related post to be loaded"
        assert p.title == 'CP Post', "Expected the related post title to match"

    async def test_post_comments_empty(self, async_blog_fixtures):
        """Post with no comments → .comments() returns [] (async)."""
        AsyncUser, AsyncPost, _ = async_blog_fixtures
        user = AsyncUser(username='abe_empty', email='abe_empty@example.com', age=25)
        await user.save()
        post = AsyncPost(title='BE Empty', content='x', user_id=user.id, status='published')
        await post.save()

        result = await AsyncPost.query().with_('comments').where(AsyncPost.c.id == post.id).one()
        assert result is not None, "Expected the post to be loaded"
        assert await result.comments() == [], "Expected the post to have no comments"


# ---------------------------------------------------------------------------
# 9. User.comments HasMany eager loading
# ---------------------------------------------------------------------------
class TestAsyncUserCommentsEager:
    """Async: verify User.comments HasMany eager loading."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_user_comments_eager(self, async_blog_fixtures):
        """with_('comments') on User should preload HasMany comments (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='auc_user', email='auc_user@example.com', age=25)
        await user.save()
        post = AsyncPost(title='AUC Post', content='x', user_id=user.id, status='published')
        await post.save()
        for i in range(3):
            c = AsyncComment(content=f'AUC {i}', user_id=user.id, post_id=post.id)
            await c.save()

        result = await AsyncUser.query().with_('comments').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        comments = await result.comments()
        assert len(comments) == 3, "Expected three related comments"

    async def test_user_comments_count(self, async_blog_fixtures):
        """with_('comments') → 2 queries regardless of N (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='auc_count', email='auc_count@example.com', age=25)
        await user.save()
        post1 = AsyncPost(title='AUC Post 1', content='x', user_id=user.id, status='published')
        await post1.save()
        post2 = AsyncPost(title='AUC Post 2', content='x', user_id=user.id, status='published')
        await post2.save()
        for i in range(4):
            c = AsyncComment(content=f'AUC C {i}', user_id=user.id, post_id=post1.id)
            await c.save()

        counter = self._install_counter(AsyncUser)
        results = await AsyncUser.query().with_('comments').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1, "Expected exactly one result"
        assert len(await results[0].comments()) == 4, "Expected four related comments"
        assert counter.select_count == 2, f"Expected 2 queries, got {counter.select_count}"


# ---------------------------------------------------------------------------
# 10. Nested eager loading: posts.comments (dot-path) — end-to-end SQL execution
# ---------------------------------------------------------------------------
class TestAsyncNestedEagerLoading:
    """Async: verify dot-path nested eager loading."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_nested_posts_comments(self, async_blog_fixtures):
        """with_('posts.comments') preloads HasMany(HasMany) in 3 queries (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='ane_user', email='ane_user@example.com', age=25)
        await user.save()
        for pi in range(3):
            post = AsyncPost(title=f'ANE Post {pi}', content=f'Content {pi}',
                             user_id=user.id, status='published')
            await post.save()
            for ci in range(2):
                c = AsyncComment(content=f'ANE C {pi}-{ci}', user_id=user.id, post_id=post.id)
                await c.save()

        counter = self._install_counter(AsyncUser)
        results = await AsyncUser.query().with_('posts.comments').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1, "Expected exactly one result"
        posts = await results[0].posts()
        assert len(posts) == 3, "Expected three related posts"
        for p in posts:
            assert len(await p.comments()) == 2, "Expected two comments per post"
        assert counter.select_count == 3, f"Expected 3 queries (user + posts + comments), got {counter.select_count}"

    async def test_nested_posts_comments_empty_posts(self, async_blog_fixtures):
        """User with no posts → posts() returns [], no batch for comments (async)."""
        AsyncUser, _, _ = async_blog_fixtures
        user = AsyncUser(username='ane_empty', email='ane_empty@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('posts.comments').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        assert await result.posts() == [], "Expected the user to have no posts"

    async def test_nested_posts_comments_no_comments(self, async_blog_fixtures):
        """Post with no comments → comments() returns [] for each post (async)."""
        AsyncUser, AsyncPost, _ = async_blog_fixtures
        user = AsyncUser(username='ane_nocom', email='ane_nocom@example.com', age=25)
        await user.save()
        for pi in range(2):
            post = AsyncPost(title=f'ANE Post {pi}', content=f'Content {pi}',
                             user_id=user.id, status='published')
            await post.save()

        result = await AsyncUser.query().with_('posts.comments').where(AsyncUser.c.id == user.id).one()
        assert result is not None, "Expected the user to be loaded"
        posts = await result.posts()
        assert len(posts) == 2, "Expected two related posts"
        for p in posts:
            assert await p.comments() == [], "Expected each post to have no comments"

    async def test_nested_posts_comments_eager_vs_lazy(self, async_blog_fixtures):
        """Eager dot-path and lazy produce identical data (async)."""
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures
        user = AsyncUser(username='ane_parity', email='ane_parity@example.com', age=30)
        await user.save()
        for pi in range(2):
            post = AsyncPost(title=f'ANE P {pi}', content=f'C {pi}',
                             user_id=user.id, status='published')
            await post.save()
            for ci in range(2):
                c = AsyncComment(content=f'ANE {pi}-{ci}', user_id=user.id, post_id=post.id)
                await c.save()

        eager = await AsyncUser.query().with_('posts.comments').where(AsyncUser.c.id == user.id).one()
        eager_posts = sorted(await eager.posts(), key=lambda p: p.id)
        eager_comments = []
        for p in eager_posts:
            eager_comments.extend(await p.comments())

        lazy_user = await AsyncUser.find_one(user.id)
        lazy_posts = sorted(await lazy_user.posts(), key=lambda p: p.id)
        lazy_comments = []
        for p in lazy_posts:
            lazy_comments.extend(await p.comments())

        assert len(eager_comments) == len(lazy_comments), \
            "Expected eager and lazy to return the same number of comments"
        for ec, lc in zip(sorted(eager_comments, key=lambda c: c.id),
                          sorted(lazy_comments, key=lambda c: c.id)):
            assert ec.content == lc.content, \
                "Expected eager and lazy comment contents to match"
