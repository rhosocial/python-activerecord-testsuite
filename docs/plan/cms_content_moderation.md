# CMS系统 - 内容审核测试实施方案

## 测试目标

验证内容审核系统，包括审核队列管理、审批工作流、评论审核、内容标记、批量审核操作和审核统计等功能。

## Provider 接口定义

### ICMSModerationProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ICMSModerationProvider(ABC):
    """CMS内容审核测试数据提供者接口"""
    
    @abstractmethod
    def setup_moderation_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Article
        Type[ActiveRecord],  # Comment
        Type[ActiveRecord],  # ModerationQueue
        Type[ActiveRecord],  # ModerationAction
        Type[ActiveRecord],  # ContentFlag
        Type[ActiveRecord]   # ModerationLog
    ]:
        """设置审核相关模型"""
        pass
    
    @abstractmethod
    def create_pending_content(
        self,
        article_count: int,
        comment_count: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建待审核内容"""
        pass
    
    @abstractmethod
    def create_moderators(
        self,
        moderator_count: int
    ) -> List[Dict]:
        """创建审核员"""
        pass
    
    @abstractmethod
    def create_flagged_content(
        self,
        flag_count: int
    ) -> List[Dict]:
        """创建已标记内容"""
        pass
    
    @abstractmethod
    def cleanup_moderation_data(self, scenario: str):
        """清理审核测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def moderation_models(request):
    """提供审核模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_cms_moderation_provider()
    
    models = provider.setup_moderation_models(scenario)
    yield models
    
    provider.cleanup_moderation_data(scenario)

@pytest.fixture
def User(moderation_models):
    """用户模型"""
    return moderation_models[0]

@pytest.fixture
def Article(moderation_models):
    """文章模型"""
    return moderation_models[1]

@pytest.fixture
def Comment(moderation_models):
    """评论模型"""
    return moderation_models[2]

@pytest.fixture
def ModerationQueue(moderation_models):
    """审核队列模型"""
    return moderation_models[3]

@pytest.fixture
def ModerationAction(moderation_models):
    """审核操作模型"""
    return moderation_models[4]

@pytest.fixture
def ContentFlag(moderation_models):
    """内容标记模型"""
    return moderation_models[5]

@pytest.fixture
def ModerationLog(moderation_models):
    """审核日志模型"""
    return moderation_models[6]

@pytest.fixture
def test_moderator(User):
    """测试审核员"""
    moderator = User(
        username="test_moderator",
        email="moderator@test.com",
        role="moderator",
        is_active=True
    )
    moderator.save()
    return moderator

@pytest.fixture
def test_author(User):
    """测试作者"""
    author = User(
        username="test_author",
        email="author@test.com",
        role="author",
        is_active=True
    )
    author.save()
    return author

@pytest.fixture
def pending_articles(request, Article, test_author):
    """待审核文章"""
    provider = get_cms_moderation_provider()
    articles, _ = provider.create_pending_content(
        article_count=10,
        comment_count=0
    )
    return articles

@pytest.fixture
def pending_comments(request, Comment, Article, test_author):
    """待审核评论"""
    provider = get_cms_moderation_provider()
    _, comments = provider.create_pending_content(
        article_count=0,
        comment_count=20
    )
    return comments
```

## 测试类和函数签名

### TestModerationQueue - 审核队列测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestModerationQueue:
    """审核队列管理测试"""
    
    def test_get_pending_content_queue(self, ModerationQueue, pending_articles):
        """测试获取待审核内容队列"""
        pass
    
    def test_queue_prioritization(self, ModerationQueue, pending_articles):
        """测试队列优先级排序"""
        pass
    
    def test_queue_filtering(self, ModerationQueue, pending_articles):
        """测试队列筛选（按类型、作者等）"""
        pass
    
    def test_queue_assignment(self, ModerationQueue, User, test_moderator):
        """测试分配审核任务"""
        pass
    
    def test_queue_statistics(self, ModerationQueue, pending_articles, pending_comments):
        """测试队列统计信息"""
        pass
    
    def test_queue_aging_items(self, ModerationQueue, pending_articles):
        """测试长期待审核内容"""
        pass
```

### TestArticleModeration - 文章审核测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestArticleModeration:
    """文章审核测试"""
    
    def test_approve_article(self, Article, ModerationAction, test_moderator, pending_articles):
        """测试批准文章"""
        pass
    
    def test_reject_article(self, Article, ModerationAction, test_moderator, pending_articles):
        """测试拒绝文章"""
        pass
    
    def test_approve_with_changes(self, Article, ModerationAction, test_moderator):
        """测试修改后批准"""
        pass
    
    def test_request_revision(self, Article, ModerationAction, test_moderator, test_author):
        """测试请求修订"""
        pass
    
    def test_moderation_notes(self, Article, ModerationAction, test_moderator):
        """测试审核备注"""
        pass
```

### TestCommentModeration - 评论审核测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestCommentModeration:
    """评论审核测试"""
    
    def test_approve_comment(self, Comment, ModerationAction, test_moderator, pending_comments):
        """测试批准评论"""
        pass
    
    def test_reject_comment(self, Comment, ModerationAction, test_moderator, pending_comments):
        """测试拒绝评论"""
        pass
    
    def test_mark_as_spam(self, Comment, ModerationAction, test_moderator):
        """测试标记为垃圾评论"""
        pass
    
    def test_nested_comment_moderation(self, Comment, ModerationAction, test_moderator):
        """测试嵌套评论审核"""
        pass
    
    def test_bulk_comment_moderation(self, Comment, ModerationAction, test_moderator, pending_comments):
        """测试批量评论审核"""
        pass
```

### TestContentFlagging - 内容标记测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestContentFlagging:
    """内容标记测试"""
    
    def test_flag_inappropriate_content(self, Article, ContentFlag, User):
        """测试标记不当内容"""
        pass
    
    def test_flag_spam(self, Comment, ContentFlag, User):
        """测试标记垃圾内容"""
        pass
    
    def test_flag_copyright_violation(self, Article, ContentFlag, User):
        """测试标记版权侵犯"""
        pass
    
    def test_flag_reasons(self, ContentFlag, Article):
        """测试标记原因分类"""
        pass
    
    def test_multiple_flags_on_content(self, Article, ContentFlag, User):
        """测试同一内容多次标记"""
        pass
    
    def test_flag_threshold_alert(self, Article, ContentFlag):
        """测试标记阈值预警"""
        pass
    
    def test_review_flagged_content(self, Article, ContentFlag, test_moderator):
        """测试审核已标记内容"""
        pass
```

### TestBulkModeration - 批量审核测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestBulkModeration:
    """批量审核操作测试"""
    
    def test_bulk_approve_articles(self, Article, ModerationAction, test_moderator, pending_articles):
        """测试批量批准文章"""
        pass
    
    def test_bulk_reject_articles(self, Article, ModerationAction, test_moderator, pending_articles):
        """测试批量拒绝文章"""
        pass
    
    def test_bulk_approve_comments(self, Comment, ModerationAction, test_moderator, pending_comments):
        """测试批量批准评论"""
        pass
    
    def test_bulk_delete_spam(self, Comment, ModerationAction, test_moderator):
        """测试批量删除垃圾内容"""
        pass
    
    def test_bulk_operation_transaction(self, Article, ModerationAction, test_moderator):
        """测试批量操作的事务性"""
        pass
    
    def test_bulk_operation_performance(self, Article, ModerationAction, test_moderator):
        """测试批量操作性能"""
        pass
```

### TestModerationWorkflow - 审核工作流测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
@pytest.mark.workflow
class TestModerationWorkflow:
    """审核工作流测试"""
    
    def test_submit_for_moderation(self, Article, ModerationQueue, test_author):
        """测试提交审核"""
        pass
    
    def test_assign_to_moderator(self, ModerationQueue, test_moderator):
        """测试分配给审核员"""
        pass
    
    def test_moderator_claim_item(self, ModerationQueue, test_moderator):
        """测试审核员认领任务"""
        pass
    
    def test_escalate_to_senior_moderator(self, ModerationQueue, User):
        """测试上报高级审核员"""
        pass
    
    def test_workflow_notifications(self, Article, ModerationAction, User, test_moderator, test_author):
        """测试工作流通知"""
        pass
    
    def test_moderation_deadline(self, ModerationQueue):
        """测试审核期限"""
        pass
```

### TestAutoModeration - 自动审核测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestAutoModeration:
    """自动审核测试"""
    
    def test_auto_approve_trusted_user(self, Article, User):
        """测试自动批准信任用户内容"""
        pass
    
    def test_auto_reject_blacklisted_keywords(self, Comment, ContentFlag):
        """测试自动拒绝黑名单关键词"""
        pass
    
    def test_spam_filter(self, Comment, ContentFlag):
        """测试垃圾内容过滤"""
        pass
    
    def test_profanity_detection(self, Comment, ContentFlag):
        """测试敏感词检测"""
        pass
    
    def test_auto_moderation_rules(self, Article, ModerationAction):
        """测试自动审核规则"""
        pass
```

### TestModerationStatistics - 审核统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestModerationStatistics:
    """审核统计测试"""
    
    def test_moderation_summary(self, ModerationAction, test_moderator):
        """测试审核摘要统计"""
        pass
    
    def test_moderator_performance(self, ModerationAction, test_moderator):
        """测试审核员绩效"""
        pass
    
    def test_approval_rejection_rates(self, ModerationAction):
        """测试批准/拒绝率"""
        pass
    
    def test_average_moderation_time(self, ModerationAction, ModerationQueue):
        """测试平均审核时间"""
        pass
    
    def test_content_type_statistics(self, ModerationAction):
        """测试按内容类型统计"""
        pass
    
    def test_flag_statistics(self, ContentFlag):
        """测试标记统计"""
        pass
```

### TestModerationLog - 审核日志测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestModerationLog:
    """审核日志测试"""
    
    def test_log_moderation_action(self, ModerationLog, ModerationAction, test_moderator):
        """测试记录审核操作"""
        pass
    
    def test_log_content_changes(self, ModerationLog, Article, test_moderator):
        """测试记录内容修改"""
        pass
    
    def test_audit_trail(self, ModerationLog, Article):
        """测试审计追踪"""
        pass
    
    def test_log_retention(self, ModerationLog):
        """测试日志保留策略"""
        pass
    
    def test_log_search(self, ModerationLog, test_moderator):
        """测试日志搜索"""
        pass
```

### TestModerationPermissions - 审核权限测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestModerationPermissions:
    """审核权限测试"""
    
    def test_moderator_permissions(self, ModerationAction, User, test_moderator):
        """测试审核员权限"""
        pass
    
    def test_admin_override(self, ModerationAction, User):
        """测试管理员覆盖"""
        pass
    
    def test_author_cannot_moderate_own(self, Article, ModerationAction, test_author):
        """测试作者不能审核自己的内容"""
        pass
    
    def test_permission_based_queue_access(self, ModerationQueue, User):
        """测试基于权限的队列访问"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **审核队列**
   - 队列获取
   - 优先级排序
   - 队列筛选
   - 任务分配
   - 队列统计
   - 超期内容

2. **文章审核**
   - 批准/拒绝
   - 修改后批准
   - 请求修订
   - 审核备注

3. **评论审核**
   - 批准/拒绝
   - 垃圾标记
   - 嵌套评论审核
   - 批量审核

4. **内容标记**
   - 不当内容标记
   - 垃圾/版权侵犯标记
   - 标记原因
   - 多次标记
   - 阈值预警
   - 标记审核

5. **批量操作**
   - 批量批准/拒绝
   - 批量删除
   - 事务处理
   - 性能优化

6. **审核工作流**
   - 提交审核
   - 任务分配/认领
   - 上报机制
   - 通知系统
   - 审核期限

7. **自动审核**
   - 信任用户自动批准
   - 黑名单自动拒绝
   - 垃圾过滤
   - 敏感词检测
   - 规则引擎

8. **审核统计**
   - 摘要统计
   - 审核员绩效
   - 批准/拒绝率
   - 平均时间
   - 类型统计
   - 标记统计

9. **审核日志**
   - 操作记录
   - 内容修改追踪
   - 审计追踪
   - 日志保留
   - 日志搜索

10. **权限管理**
    - 审核员权限
    - 管理员覆盖
    - 自审限制
    - 队列访问控制

### 所需能力（Capabilities）

- **批量操作**：批量审核处理
- **事务支持**：批量操作的原子性
- **关系加载**：评论树结构（嵌套评论）
- **聚合函数**：审核统计、绩效计算
- **查询构建**：复杂的队列筛选、日志搜索

### 测试数据规模

- 审核员：3-10 个审核员
- 待审核文章：10-50 篇
- 待审核评论：20-100 条
- 内容标记：10-50 个标记
- 审核日志：100-500 条记录

### 性能预期

- 队列加载：< 100ms（100条待审核内容）
- 单个审核操作：< 50ms
- 批量审核（100条）：< 1s
- 审核统计查询：< 200ms
- 日志搜索：< 300ms
- 自动审核处理：< 10ms/条
