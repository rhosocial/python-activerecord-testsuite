# 社交网络 - 社交图谱测试实施方案

## 测试目标

验证社交图谱系统，包括关注关系管理、粉丝列表、共同好友查找、连接建议、隐私设置和用户屏蔽等核心社交网络功能。

## Provider 接口定义

### ISocialGraphProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ISocialGraphProvider(ABC):
    """社交图谱测试数据提供者接口"""
    
    @abstractmethod
    def setup_social_graph_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Follow
        Type[ActiveRecord],  # Friendship
        Type[ActiveRecord],  # BlockedUser
        Type[ActiveRecord],  # PrivacySetting
        Type[ActiveRecord]   # ConnectionSuggestion
    ]:
        """设置社交图谱相关模型"""
        pass
    
    @abstractmethod
    def create_social_network(
        self,
        user_count: int,
        connections_per_user_range: Tuple[int, int]
    ) -> List[Dict]:
        """创建社交网络数据"""
        pass
    
    @abstractmethod
    def create_friendship_graph(
        self,
        user_count: int,
        mutual_connections_per_user: int
    ) -> List[Dict]:
        """创建好友关系图"""
        pass
    
    @abstractmethod
    def cleanup_social_graph_data(self, scenario: str):
        """清理社交图谱测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def social_graph_models(request):
    """提供社交图谱模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_social_graph_provider()
    
    models = provider.setup_social_graph_models(scenario)
    yield models
    
    provider.cleanup_social_graph_data(scenario)

@pytest.fixture
def User(social_graph_models):
    """用户模型"""
    return social_graph_models[0]

@pytest.fixture
def Follow(social_graph_models):
    """关注关系模型"""
    return social_graph_models[1]

@pytest.fixture
def Friendship(social_graph_models):
    """好友关系模型"""
    return social_graph_models[2]

@pytest.fixture
def BlockedUser(social_graph_models):
    """屏蔽用户模型"""
    return social_graph_models[3]

@pytest.fixture
def PrivacySetting(social_graph_models):
    """隐私设置模型"""
    return social_graph_models[4]

@pytest.fixture
def ConnectionSuggestion(social_graph_models):
    """连接建议模型"""
    return social_graph_models[5]

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
    for i in range(10):
        user = User(
            username=f"test_user_{i}",
            email=f"user{i}@test.com",
            is_active=True
        )
        user.save()
        users.append(user)
    return users

@pytest.fixture
def social_network(request, User, Follow):
    """社交网络数据"""
    provider = get_social_graph_provider()
    network = provider.create_social_network(
        user_count=50,
        connections_per_user_range=(5, 20)
    )
    return network
```

## 测试类和函数签名

### TestFollowRelationship - 关注关系测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFollowRelationship:
    """关注关系测试"""
    
    def test_follow_user(self, User, Follow, test_user, test_users):
        """测试关注用户"""
        pass
    
    def test_unfollow_user(self, User, Follow, test_user, test_users):
        """测试取消关注"""
        pass
    
    def test_cannot_follow_self(self, User, Follow, test_user):
        """测试不能关注自己"""
        pass
    
    def test_duplicate_follow_prevention(self, User, Follow, test_user, test_users):
        """测试防止重复关注"""
        pass
    
    def test_follow_blocked_user(self, User, Follow, BlockedUser, test_users):
        """测试关注已屏蔽用户（应失败）"""
        pass
    
    def test_bidirectional_follow(self, User, Follow, test_users):
        """测试双向关注"""
        pass
```

### TestFollowerLists - 粉丝列表测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFollowerLists:
    """粉丝列表测试"""
    
    def test_get_followers(self, User, Follow, test_user, test_users):
        """测试获取粉丝列表"""
        pass
    
    def test_get_following(self, User, Follow, test_user, test_users):
        """测试获取关注列表"""
        pass
    
    def test_follower_count(self, User, Follow, test_user, test_users):
        """测试粉丝数统计"""
        pass
    
    def test_following_count(self, User, Follow, test_user, test_users):
        """测试关注数统计"""
        pass
    
    def test_is_following(self, User, Follow, test_users):
        """测试检查是否关注"""
        pass
    
    def test_is_followed_by(self, User, Follow, test_users):
        """测试检查是否被关注"""
        pass
    
    def test_followers_pagination(self, User, Follow, social_network):
        """测试粉丝列表分页"""
        pass
```

### TestMutualFriends - 共同好友测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
@requires_capabilities((CapabilityCategory.CTE, CTECapability.BASIC_CTE))
class TestMutualFriends:
    """共同好友测试"""
    
    def test_find_mutual_followers(self, User, Follow, test_users):
        """测试查找共同粉丝"""
        pass
    
    def test_find_mutual_following(self, User, Follow, test_users):
        """测试查找共同关注"""
        pass
    
    def test_mutual_friends_count(self, User, Follow, test_users):
        """测试共同好友数量"""
        pass
    
    def test_friendship_strength(self, User, Follow, Friendship):
        """测试好友关系强度"""
        pass
```

### TestFriendshipGraph - 好友关系图测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
@requires_capabilities((CapabilityCategory.CTE, CTECapability.RECURSIVE_CTE))
class TestFriendshipGraph:
    """好友关系图测试"""
    
    def test_first_degree_connections(self, User, Follow, test_user, test_users):
        """测试一度连接"""
        pass
    
    def test_second_degree_connections(self, User, Follow, test_user, social_network):
        """测试二度连接"""
        pass
    
    def test_nth_degree_connections(self, User, Follow, social_network):
        """测试N度连接"""
        pass
    
    def test_shortest_path_between_users(self, User, Follow, social_network):
        """测试用户间最短路径"""
        pass
    
    def test_degrees_of_separation(self, User, Follow, social_network):
        """测试分离度数（六度分离理论）"""
        pass
    
    def test_connection_path(self, User, Follow, social_network):
        """测试连接路径"""
        pass
```

### TestConnectionSuggestions - 连接建议测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestConnectionSuggestions:
    """连接建议测试"""
    
    def test_suggest_mutual_friends(self, User, Follow, ConnectionSuggestion, test_user):
        """测试基于共同好友的建议"""
        pass
    
    def test_suggest_similar_interests(self, User, ConnectionSuggestion):
        """测试基于相似兴趣的建议"""
        pass
    
    def test_suggest_popular_users(self, User, Follow, ConnectionSuggestion):
        """测试热门用户建议"""
        pass
    
    def test_suggest_nearby_users(self, User, ConnectionSuggestion):
        """测试附近用户建议"""
        pass
    
    def test_suggestion_ranking(self, ConnectionSuggestion, test_user):
        """测试建议排序"""
        pass
    
    def test_dismiss_suggestion(self, ConnectionSuggestion, test_user):
        """测试忽略建议"""
        pass
    
    def test_exclude_blocked_users(self, User, BlockedUser, ConnectionSuggestion):
        """测试排除已屏蔽用户"""
        pass
```

### TestPrivacySettings - 隐私设置测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestPrivacySettings:
    """隐私设置测试"""
    
    def test_set_profile_visibility(self, User, PrivacySetting, test_user):
        """测试设置资料可见性"""
        pass
    
    def test_set_follower_visibility(self, User, PrivacySetting, test_user):
        """测试设置粉丝列表可见性"""
        pass
    
    def test_set_following_visibility(self, User, PrivacySetting, test_user):
        """测试设置关注列表可见性"""
        pass
    
    def test_privacy_public(self, User, PrivacySetting):
        """测试公开隐私设置"""
        pass
    
    def test_privacy_friends_only(self, User, Follow, PrivacySetting):
        """测试仅好友可见"""
        pass
    
    def test_privacy_private(self, User, PrivacySetting):
        """测试私密隐私设置"""
        pass
    
    def test_custom_privacy_lists(self, User, PrivacySetting):
        """测试自定义隐私列表"""
        pass
    
    def test_check_view_permission(self, User, PrivacySetting, Follow):
        """测试查看权限检查"""
        pass
```

### TestUserBlocking - 用户屏蔽测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestUserBlocking:
    """用户屏蔽测试"""
    
    def test_block_user(self, User, BlockedUser, test_user, test_users):
        """测试屏蔽用户"""
        pass
    
    def test_unblock_user(self, User, BlockedUser, test_user, test_users):
        """测试取消屏蔽"""
        pass
    
    def test_blocked_user_cannot_follow(self, User, Follow, BlockedUser):
        """测试被屏蔽用户不能关注"""
        pass
    
    def test_blocked_user_cannot_view_profile(self, User, BlockedUser, PrivacySetting):
        """测试被屏蔽用户不能查看资料"""
        pass
    
    def test_blocked_user_list(self, User, BlockedUser, test_user):
        """测试屏蔽用户列表"""
        pass
    
    def test_mutual_blocking(self, User, BlockedUser, test_users):
        """测试双向屏蔽"""
        pass
    
    def test_unfollow_on_block(self, User, Follow, BlockedUser):
        """测试屏蔽时取消关注关系"""
        pass
```

### TestFollowNotifications - 关注通知测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFollowNotifications:
    """关注通知测试"""
    
    def test_notify_on_new_follower(self, User, Follow):
        """测试新粉丝通知"""
        pass
    
    def test_notify_on_follow_back(self, User, Follow):
        """测试回关通知"""
        pass
    
    def test_notification_preferences(self, User, PrivacySetting):
        """测试通知偏好设置"""
        pass
    
    def test_batch_notifications(self, User, Follow):
        """测试批量通知"""
        pass
```

### TestSocialGraphStatistics - 社交图谱统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestSocialGraphStatistics:
    """社交图谱统计测试"""
    
    def test_network_size(self, User, Follow, social_network):
        """测试网络规模统计"""
        pass
    
    def test_average_connections(self, User, Follow, social_network):
        """测试平均连接数"""
        pass
    
    def test_most_followed_users(self, User, Follow, social_network):
        """测试最多粉丝用户"""
        pass
    
    def test_most_active_users(self, User, Follow):
        """测试最活跃用户"""
        pass
    
    def test_network_density(self, User, Follow, social_network):
        """测试网络密度"""
        pass
    
    def test_clustering_coefficient(self, User, Follow, social_network):
        """测试聚类系数"""
        pass
```

### TestFollowPerformance - 关注性能测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestFollowPerformance:
    """关注操作性能测试"""
    
    def test_follow_operation_speed(self, User, Follow):
        """测试关注操作速度"""
        pass
    
    def test_follower_list_query_performance(self, User, Follow, social_network):
        """测试粉丝列表查询性能"""
        pass
    
    def test_large_follower_count_handling(self, User, Follow):
        """测试大量粉丝处理"""
        pass
    
    def test_concurrent_follow_operations(self, User, Follow):
        """测试并发关注操作"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **关注关系**
   - 关注用户
   - 取消关注
   - 防止自我关注
   - 重复关注防护
   - 屏蔽用户限制
   - 双向关注

2. **粉丝列表**
   - 粉丝列表
   - 关注列表
   - 粉丝/关注计数
   - 关注状态检查
   - 列表分页

3. **共同好友**
   - 共同粉丝查找
   - 共同关注查找
   - 共同好友计数
   - 好友关系强度

4. **好友关系图**
   - 一度连接
   - 二度连接
   - N度连接
   - 最短路径
   - 分离度数
   - 连接路径

5. **连接建议**
   - 共同好友建议
   - 相似兴趣建议
   - 热门用户建议
   - 附近用户建议
   - 建议排序
   - 忽略建议
   - 屏蔽用户排除

6. **隐私设置**
   - 资料可见性
   - 粉丝列表可见性
   - 关注列表可见性
   - 公开/好友/私密模式
   - 自定义隐私列表
   - 查看权限检查

7. **用户屏蔽**
   - 屏蔽用户
   - 取消屏蔽
   - 关注限制
   - 资料查看限制
   - 屏蔽列表
   - 双向屏蔽
   - 自动取消关注

8. **关注通知**
   - 新粉丝通知
   - 回关通知
   - 通知偏好
   - 批量通知

9. **社交统计**
   - 网络规模
   - 平均连接数
   - 最多粉丝
   - 最活跃用户
   - 网络密度
   - 聚类系数

10. **性能优化**
    - 关注速度
    - 列表查询性能
    - 大量粉丝处理
    - 并发操作

### 所需能力（Capabilities）

- **自引用关系**：用户关注用户的自引用外键
- **CTE支持**：好友图谱查询需要递归CTE
- **聚合函数**：粉丝计数、统计分析
- **查询优化**：大规模社交网络的高效查询

### 测试数据规模

- 用户：50-200 个用户
- 关注关系：每个用户 5-50 个关注
- 好友关系：每个用户 3-20 个双向关注
- 屏蔽：5-20 个屏蔽关系
- 连接建议：每个用户 10-30 个建议

### 性能预期

- 关注操作：< 50ms
- 粉丝列表查询：< 100ms（100个粉丝，分页20条）
- 共同好友查询：< 200ms
- 二度连接查询：< 500ms
- 连接建议生成：< 1s
- 网络统计计算：< 2s（200个用户）
