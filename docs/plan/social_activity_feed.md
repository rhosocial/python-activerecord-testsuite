# 社交网络 - 活动动态测试实施方案

## 测试目标

验证社交动态系统，包括时间线生成、动态发布、动态筛选、游标分页、实时更新和动态排序等功能。

## Provider 接口定义

### ISocialFeedProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ISocialFeedProvider(ABC):
    """社交动态测试数据提供者接口"""
    
    @abstractmethod
    def setup_feed_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Post
        Type[ActiveRecord],  # Comment
        Type[ActiveRecord],  # Like
        Type[ActiveRecord],  # Share
        Type[ActiveRecord],  # Follow
        Type[ActiveRecord],  # FeedItem
        Type[ActiveRecord]   # Hashtag
    ]:
        """设置动态系统相关模型"""
        pass
    
    @abstractmethod
    def create_social_posts(
        self,
        user_count: int,
        posts_per_user_range: Tuple[int, int]
    ) -> List[Dict]:
        """创建社交动态"""
        pass
    
    @abstractmethod
    def create_feed_interactions(
        self,
        post_count: int,
        interactions_per_post: int
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """创建动态互动（评论、点赞、分享）"""
        pass
    
    @abstractmethod
    def cleanup_feed_data(self, scenario: str):
        """清理动态测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def feed_models(request):
    """提供动态系统模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_social_feed_provider()
    
    models = provider.setup_feed_models(scenario)
    yield models
    
    provider.cleanup_feed_data(scenario)

@pytest.fixture
def User(feed_models):
    """用户模型"""
    return feed_models[0]

@pytest.fixture
def Post(feed_models):
    """动态模型"""
    return feed_models[1]

@pytest.fixture
def Comment(feed_models):
    """评论模型"""
    return feed_models[2]

@pytest.fixture
def Like(feed_models):
    """点赞模型"""
    return feed_models[3]

@pytest.fixture
def Share(feed_models):
    """分享模型"""
    return feed_models[4]

@pytest.fixture
def Follow(feed_models):
    """关注关系模型"""
    return feed_models[5]

@pytest.fixture
def FeedItem(feed_models):
    """动态流项目模型"""
    return feed_models[6]

@pytest.fixture
def Hashtag(feed_models):
    """话题标签模型"""
    return feed_models[7]

@pytest.fixture
def test_user(User):
    """测试用户"""
    user = User(
        username="test_user",
        email="user@test.com",
        is_active=True
    )
    user.save()
    return user

@pytest.fixture
def test_users(User):
    """多个测试用户"""
    users = []
    for i in range(20):
        user = User(
            username=f"test_user_{i}",
            email=f"user{i}@test.com",
            is_active=True
        )
        user.save()
        users.append(user)
    return users

@pytest.fixture
def social_posts(request, Post, test_users):
    """社交动态数据"""
    provider = get_social_feed_provider()
    posts = provider.create_social_posts(
        user_count=20,
        posts_per_user_range=(5, 15)
    )
    return posts
```

## 测试类和函数签名

### TestTimelineGeneration - 时间线生成测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
@requires_capabilities((CapabilityCategory.WINDOW_FUNCTIONS, WindowFunctionCapability.ROW_NUMBER))
class TestTimelineGeneration:
    """时间线生成测试"""
    
    def test_generate_home_timeline(self, User, Post, Follow, FeedItem, test_user):
        """测试生成主页时间线"""
        pass
    
    def test_timeline_from_followed_users(self, User, Post, Follow, FeedItem, test_user, test_users):
        """测试从关注用户生成时间线"""
        pass
    
    def test_timeline_chronological_order(self, FeedItem, test_user):
        """测试时间线按时间倒序"""
        pass
    
    def test_timeline_with_pinned_posts(self, Post, FeedItem, test_user):
        """测试带置顶动态的时间线"""
        pass
    
    def test_empty_timeline(self, User, FeedItem):
        """测试空时间线（无关注）"""
        pass
```

### TestPostCreation - 动态发布测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestPostCreation:
    """动态发布测试"""
    
    def test_create_text_post(self, Post, test_user):
        """测试发布文本动态"""
        pass
    
    def test_create_post_with_image(self, Post, test_user):
        """测试发布带图片动态"""
        pass
    
    def test_create_post_with_video(self, Post, test_user):
        """测试发布带视频动态"""
        pass
    
    def test_create_post_with_link(self, Post, test_user):
        """测试发布带链接动态"""
        pass
    
    def test_post_validation(self, Post, test_user):
        """测试动态内容验证"""
        pass
    
    def test_post_with_hashtags(self, Post, Hashtag, test_user):
        """测试发布带话题标签的动态"""
        pass
    
    def test_post_with_mentions(self, Post, User, test_user, test_users):
        """测试发布带@提及的动态"""
        pass
    
    def test_scheduled_post(self, Post, test_user):
        """测试定时发布动态"""
        pass
```

### TestPostSharing - 动态分享测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestPostSharing:
    """动态分享测试"""
    
    def test_share_post(self, Post, Share, test_user, test_users):
        """测试分享动态"""
        pass
    
    def test_share_with_comment(self, Post, Share, test_user):
        """测试带评论分享"""
        pass
    
    def test_reshare_count(self, Post, Share, test_users):
        """测试分享计数"""
        pass
    
    def test_share_chain(self, Post, Share, test_users):
        """测试分享链（转发的转发）"""
        pass
    
    def test_original_post_attribution(self, Post, Share):
        """测试原始动态归属"""
        pass
```

### TestFeedFiltering - 动态筛选测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFeedFiltering:
    """动态筛选测试"""
    
    def test_filter_by_visibility(self, Post, FeedItem, test_user):
        """测试按可见性筛选（公开/好友/私密）"""
        pass
    
    def test_filter_friends_only(self, Post, Follow, FeedItem, test_user):
        """测试仅好友可见筛选"""
        pass
    
    def test_filter_by_content_type(self, Post, FeedItem):
        """测试按内容类型筛选（文本/图片/视频）"""
        pass
    
    def test_filter_by_hashtag(self, Post, Hashtag, FeedItem):
        """测试按话题标签筛选"""
        pass
    
    def test_filter_by_user(self, Post, User, FeedItem):
        """测试按用户筛选"""
        pass
    
    def test_hide_posts_from_blocked_users(self, Post, User, FeedItem):
        """测试隐藏被屏蔽用户的动态"""
        pass
```

### TestCursorPagination - 游标分页测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestCursorPagination:
    """游标分页测试"""
    
    def test_initial_page(self, FeedItem, test_user):
        """测试首页加载"""
        pass
    
    def test_next_page(self, FeedItem, test_user):
        """测试下一页"""
        pass
    
    def test_previous_page(self, FeedItem, test_user):
        """测试上一页"""
        pass
    
    def test_cursor_stability(self, FeedItem, test_user):
        """测试游标稳定性（新动态不影响已加载页面）"""
        pass
    
    def test_page_size_control(self, FeedItem, test_user):
        """测试分页大小控制"""
        pass
    
    def test_end_of_feed(self, FeedItem, test_user):
        """测试动态流末尾"""
        pass
```

### TestFeedRanking - 动态排序测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
@requires_capabilities((CapabilityCategory.WINDOW_FUNCTIONS, WindowFunctionCapability.ROW_NUMBER))
class TestFeedRanking:
    """动态排序测试"""
    
    def test_chronological_ranking(self, Post, FeedItem):
        """测试时间顺序排序"""
        pass
    
    def test_engagement_ranking(self, Post, Like, Comment, Share, FeedItem):
        """测试互动度排序"""
        pass
    
    def test_relevance_ranking(self, Post, FeedItem, test_user):
        """测试相关性排序"""
        pass
    
    def test_trending_posts(self, Post, Like, Comment, FeedItem):
        """测试热门动态"""
        pass
    
    def test_personalized_ranking(self, Post, FeedItem, test_user):
        """测试个性化排序"""
        pass
```

### TestRealTimeUpdates - 实时更新测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestRealTimeUpdates:
    """实时更新测试"""
    
    def test_new_post_notification(self, Post, FeedItem, test_user):
        """测试新动态通知"""
        pass
    
    def test_poll_for_updates(self, FeedItem, test_user):
        """测试轮询更新"""
        pass
    
    def test_websocket_updates(self, Post, FeedItem):
        """测试WebSocket推送（如支持）"""
        pass
    
    def test_unread_count(self, FeedItem, test_user):
        """测试未读计数"""
        pass
    
    def test_mark_as_read(self, FeedItem, test_user):
        """测试标记为已读"""
        pass
```

### TestPostInteractions - 动态互动测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestPostInteractions:
    """动态互动测试"""
    
    def test_like_post(self, Post, Like, test_user):
        """测试点赞动态"""
        pass
    
    def test_unlike_post(self, Post, Like, test_user):
        """测试取消点赞"""
        pass
    
    def test_like_count(self, Post, Like, test_users):
        """测试点赞计数"""
        pass
    
    def test_comment_on_post(self, Post, Comment, test_user):
        """测试评论动态"""
        pass
    
    def test_reply_to_comment(self, Comment, test_user, test_users):
        """测试回复评论"""
        pass
    
    def test_comment_count(self, Post, Comment, test_users):
        """测试评论计数"""
        pass
    
    def test_save_post(self, Post, User, test_user):
        """测试收藏动态"""
        pass
```

### TestHashtagSystem - 话题标签系统测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestHashtagSystem:
    """话题标签系统测试"""
    
    def test_extract_hashtags(self, Post, Hashtag, test_user):
        """测试提取话题标签"""
        pass
    
    def test_trending_hashtags(self, Hashtag, Post):
        """测试热门话题标签"""
        pass
    
    def test_hashtag_feed(self, Post, Hashtag, FeedItem):
        """测试话题标签动态流"""
        pass
    
    def test_hashtag_statistics(self, Hashtag, Post):
        """测试话题标签统计"""
        pass
    
    def test_hashtag_autocomplete(self, Hashtag):
        """测试话题标签自动完成"""
        pass
```

### TestUserMentions - 用户提及测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestUserMentions:
    """用户提及测试"""
    
    def test_mention_user_in_post(self, Post, User, test_user, test_users):
        """测试在动态中@用户"""
        pass
    
    def test_mention_notification(self, Post, User):
        """测试@提及通知"""
        pass
    
    def test_get_mentions(self, Post, User, test_user):
        """测试获取@我的动态"""
        pass
    
    def test_mention_privacy(self, Post, User):
        """测试@提及隐私（私密动态）"""
        pass
```

### TestFeedStatistics - 动态统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFeedStatistics:
    """动态统计测试"""
    
    def test_post_engagement_rate(self, Post, Like, Comment, Share):
        """测试动态互动率"""
        pass
    
    def test_user_activity_statistics(self, User, Post):
        """测试用户活跃度统计"""
        pass
    
    def test_feed_health_metrics(self, FeedItem, test_user):
        """测试动态流健康度指标"""
        pass
    
    def test_content_type_distribution(self, Post):
        """测试内容类型分布"""
        pass
    
    def test_peak_activity_times(self, Post):
        """测试活跃高峰时段"""
        pass
```

### TestFeedPerformance - 动态流性能测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFeedPerformance:
    """动态流性能测试"""
    
    def test_timeline_generation_speed(self, FeedItem, test_user, social_posts):
        """测试时间线生成速度"""
        pass
    
    def test_large_follower_count_performance(self, User, Follow, FeedItem):
        """测试大量关注用户的性能"""
        pass
    
    def test_feed_caching(self, FeedItem, test_user):
        """测试动态流缓存"""
        pass
    
    def test_infinite_scroll_performance(self, FeedItem, test_user):
        """测试无限滚动性能"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **时间线生成**
   - 主页时间线
   - 关注用户动态
   - 时间倒序
   - 置顶动态
   - 空时间线

2. **动态发布**
   - 文本动态
   - 图片动态
   - 视频动态
   - 链接动态
   - 内容验证
   - 话题标签
   - 用户提及
   - 定时发布

3. **动态分享**
   - 分享动态
   - 带评论分享
   - 分享计数
   - 分享链
   - 原始归属

4. **动态筛选**
   - 可见性筛选
   - 好友可见
   - 内容类型
   - 话题标签
   - 用户筛选
   - 屏蔽用户隐藏

5. **游标分页**
   - 首页加载
   - 下一页/上一页
   - 游标稳定性
   - 分页大小
   - 末尾检测

6. **动态排序**
   - 时间顺序
   - 互动度排序
   - 相关性排序
   - 热门动态
   - 个性化排序

7. **实时更新**
   - 新动态通知
   - 轮询更新
   - WebSocket推送
   - 未读计数
   - 标记已读

8. **动态互动**
   - 点赞/取消点赞
   - 点赞计数
   - 评论
   - 评论回复
   - 评论计数
   - 收藏动态

9. **话题标签**
   - 标签提取
   - 热门标签
   - 标签动态流
   - 标签统计
   - 自动完成

10. **用户提及**
    - @用户
    - 提及通知
    - @我的动态
    - 提及隐私

11. **动态统计**
    - 互动率
    - 用户活跃度
    - 动态流健康度
    - 内容类型分布
    - 活跃时段

12. **性能优化**
    - 时间线生成速度
    - 大量关注处理
    - 动态流缓存
    - 无限滚动

### 所需能力（Capabilities）

- **窗口函数**：动态排序、排名计算
- **关系加载**：动态->用户、动态->评论、动态->点赞
- **聚合函数**：互动统计、计数功能
- **高效分页**：游标分页实现
- **查询优化**：大规模动态流的性能优化

### 测试数据规模

- 用户：20-100 个用户
- 动态：每个用户 5-30 条动态
- 评论：每条动态 0-20 条评论
- 点赞：每条动态 0-50 个点赞
- 分享：每条动态 0-10 次分享
- 话题标签：50-200 个标签

### 性能预期

- 时间线生成：< 200ms（100个关注，20条/页）
- 动态发布：< 100ms
- 点赞操作：< 30ms
- 评论发布：< 100ms
- 分页加载：< 100ms
- 话题标签动态流：< 200ms
- 实时更新轮询：< 50ms
- 大量关注（500+）时间线：< 1s
