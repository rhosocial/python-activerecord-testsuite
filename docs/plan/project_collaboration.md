# 项目管理 - 协作功能测试实施方案

## 测试目标

验证项目协作功能，包括任务评论、@提及、文件附件、活动动态、实时更新和通知系统等功能。

## Provider 接口定义

### IProjectCollaborationProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class IProjectCollaborationProvider(ABC):
    """项目协作测试数据提供者接口"""
    
    @abstractmethod
    def setup_collaboration_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Project
        Type[ActiveRecord],  # Task
        Type[ActiveRecord],  # Comment
        Type[ActiveRecord],  # Mention
        Type[ActiveRecord],  # Attachment
        Type[ActiveRecord],  # Activity
        Type[ActiveRecord]   # Notification
    ]:
        """设置协作功能相关模型"""
        pass
    
    @abstractmethod
    def create_collaboration_data(
        self,
        project_count: int,
        users_per_project: int,
        comments_per_task: int
    ) -> List[Dict]:
        """创建协作数据"""
        pass
    
    @abstractmethod
    def cleanup_collaboration_data(self, scenario: str):
        """清理协作测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def collaboration_models(request):
    """提供协作功能模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_project_collaboration_provider()
    
    models = provider.setup_collaboration_models(scenario)
    yield models
    
    provider.cleanup_collaboration_data(scenario)

@pytest.fixture
def User(collaboration_models):
    """用户模型"""
    return collaboration_models[0]

@pytest.fixture
def Project(collaboration_models):
    """项目模型"""
    return collaboration_models[1]

@pytest.fixture
def Task(collaboration_models):
    """任务模型"""
    return collaboration_models[2]

@pytest.fixture
def Comment(collaboration_models):
    """评论模型"""
    return collaboration_models[3]

@pytest.fixture
def Mention(collaboration_models):
    """提及模型"""
    return collaboration_models[4]

@pytest.fixture
def Attachment(collaboration_models):
    """附件模型"""
    return collaboration_models[5]

@pytest.fixture
def Activity(collaboration_models):
    """活动模型"""
    return collaboration_models[6]

@pytest.fixture
def Notification(collaboration_models):
    """通知模型"""
    return collaboration_models[7]

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
    for i in range(5):
        user = User(
            username=f"test_user_{i}",
            email=f"user{i}@test.com",
            is_active=True
        )
        user.save()
        users.append(user)
    return users

@pytest.fixture
def test_project(Project, test_user):
    """测试项目"""
    project = Project(
        name="Test Project",
        owner_id=test_user.id,
        is_active=True
    )
    project.save()
    return project

@pytest.fixture
def test_task(Task, test_project, test_user):
    """测试任务"""
    task = Task(
        title="Test Task",
        project_id=test_project.id,
        assignee_id=test_user.id,
        status="in_progress"
    )
    task.save()
    return task
```

## 测试类和函数签名

### TestTaskCommenting - 任务评论测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTaskCommenting:
    """任务评论测试"""
    
    def test_add_comment_to_task(self, Comment, test_task, test_user):
        """测试添加任务评论"""
        pass
    
    def test_reply_to_comment(self, Comment, test_task, test_users):
        """测试回复评论"""
        pass
    
    def test_edit_comment(self, Comment, test_task, test_user):
        """测试编辑评论"""
        pass
    
    def test_delete_comment(self, Comment, test_task, test_user):
        """测试删除评论"""
        pass
    
    def test_comment_thread(self, Comment, test_task, test_users):
        """测试评论线程"""
        pass
    
    def test_comment_with_markdown(self, Comment, test_task, test_user):
        """测试Markdown格式评论"""
        pass
    
    def test_comment_history(self, Comment, test_task):
        """测试评论历史"""
        pass
```

### TestMentions - @提及测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestMentions:
    """@提及测试"""
    
    def test_mention_user_in_comment(self, Comment, Mention, test_task, test_users):
        """测试在评论中@用户"""
        pass
    
    def test_mention_user_in_task_description(self, Task, Mention, test_project, test_users):
        """测试在任务描述中@用户"""
        pass
    
    def test_mention_notification(self, Comment, Mention, Notification, test_users):
        """测试@提及通知"""
        pass
    
    def test_multiple_mentions(self, Comment, Mention, test_task, test_users):
        """测试多个@提及"""
        pass
    
    def test_mention_autocomplete(self, Mention, User):
        """测试@提及自动完成"""
        pass
    
    def test_get_mentions(self, Mention, test_user):
        """测试获取@我的内容"""
        pass
```

### TestFileAttachments - 文件附件测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestFileAttachments:
    """文件附件测试"""
    
    def test_attach_file_to_task(self, Attachment, test_task, test_user):
        """测试附加文件到任务"""
        pass
    
    def test_attach_file_to_comment(self, Attachment, Comment, test_task, test_user):
        """测试附加文件到评论"""
        pass
    
    def test_attach_multiple_files(self, Attachment, test_task, test_user):
        """测试附加多个文件"""
        pass
    
    def test_file_validation(self, Attachment, test_task, test_user):
        """测试文件验证（格式、大小）"""
        pass
    
    def test_download_attachment(self, Attachment, test_task):
        """测试下载附件"""
        pass
    
    def test_remove_attachment(self, Attachment, test_task, test_user):
        """测试移除附件"""
        pass
    
    def test_attachment_preview(self, Attachment, test_task):
        """测试附件预览"""
        pass
    
    def test_attachment_versioning(self, Attachment, test_task, test_user):
        """测试附件版本管理"""
        pass
```

### TestActivityFeed - 活动动态测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestActivityFeed:
    """活动动态测试"""
    
    def test_record_task_creation(self, Activity, test_task):
        """测试记录任务创建"""
        pass
    
    def test_record_task_update(self, Activity, test_task, test_user):
        """测试记录任务更新"""
        pass
    
    def test_record_comment_activity(self, Activity, Comment, test_task):
        """测试记录评论活动"""
        pass
    
    def test_record_assignment_change(self, Activity, test_task, test_users):
        """测试记录分配变更"""
        pass
    
    def test_project_activity_feed(self, Activity, test_project):
        """测试项目活动流"""
        pass
    
    def test_task_activity_feed(self, Activity, test_task):
        """测试任务活动流"""
        pass
    
    def test_user_activity_feed(self, Activity, test_user):
        """测试用户活动流"""
        pass
    
    def test_activity_filtering(self, Activity, test_project):
        """测试活动筛选"""
        pass
```

### TestRealTimeUpdates - 实时更新测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestRealTimeUpdates:
    """实时更新测试"""
    
    def test_task_update_broadcast(self, Task, test_users):
        """测试任务更新广播"""
        pass
    
    def test_comment_notification(self, Comment, test_task, test_users):
        """测试评论实时通知"""
        pass
    
    def test_assignment_notification(self, Task, test_users):
        """测试分配实时通知"""
        pass
    
    def test_online_user_presence(self, User, test_project):
        """测试在线用户状态"""
        pass
    
    def test_typing_indicator(self, Comment, test_task, test_users):
        """测试正在输入指示器"""
        pass
```

### TestNotificationSystem - 通知系统测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestNotificationSystem:
    """通知系统测试"""
    
    def test_task_assignment_notification(self, Notification, test_task, test_user):
        """测试任务分配通知"""
        pass
    
    def test_comment_notification(self, Notification, Comment, test_task, test_users):
        """测试评论通知"""
        pass
    
    def test_mention_notification(self, Notification, Mention, test_users):
        """测试@提及通知"""
        pass
    
    def test_due_date_notification(self, Notification, test_task):
        """测试截止日期通知"""
        pass
    
    def test_notification_preferences(self, User, Notification, test_user):
        """测试通知偏好设置"""
        pass
    
    def test_mark_notification_read(self, Notification, test_user):
        """测试标记通知为已读"""
        pass
    
    def test_bulk_mark_read(self, Notification, test_user):
        """测试批量标记已读"""
        pass
    
    def test_notification_grouping(self, Notification, test_user):
        """测试通知分组"""
        pass
```

### TestDiscussionThreads - 讨论线程测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestDiscussionThreads:
    """讨论线程测试"""
    
    def test_create_discussion(self, Comment, test_project, test_user):
        """测试创建讨论"""
        pass
    
    def test_discussion_participants(self, Comment, test_users):
        """测试讨论参与者"""
        pass
    
    def test_resolve_discussion(self, Comment, test_task, test_user):
        """测试解决讨论"""
        pass
    
    def test_reopen_discussion(self, Comment, test_task, test_user):
        """测试重新打开讨论"""
        pass
    
    def test_pin_discussion(self, Comment, test_task, test_user):
        """测试置顶讨论"""
        pass
```

### TestWatching - 关注功能测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestWatching:
    """关注功能测试"""
    
    def test_watch_task(self, Task, User, test_task, test_user):
        """测试关注任务"""
        pass
    
    def test_unwatch_task(self, Task, User, test_task, test_user):
        """测试取消关注任务"""
        pass
    
    def test_watch_project(self, Project, User, test_project, test_user):
        """测试关注项目"""
        pass
    
    def test_auto_watch_on_participation(self, Task, User, Comment, test_users):
        """测试参与后自动关注"""
        pass
    
    def test_watcher_notifications(self, Task, Notification, test_users):
        """测试关注者通知"""
        pass
```

### TestCollaborationPermissions - 协作权限测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestCollaborationPermissions:
    """协作权限测试"""
    
    def test_comment_permission(self, Comment, test_task, User):
        """测试评论权限"""
        pass
    
    def test_edit_own_comment(self, Comment, test_task, test_user):
        """测试编辑自己的评论"""
        pass
    
    def test_cannot_edit_others_comment(self, Comment, test_task, test_users):
        """测试不能编辑他人评论"""
        pass
    
    def test_admin_edit_permission(self, Comment, User):
        """测试管理员编辑权限"""
        pass
    
    def test_attachment_permission(self, Attachment, test_task, User):
        """测试附件权限"""
        pass
```

### TestCollaborationStatistics - 协作统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestCollaborationStatistics:
    """协作统计测试"""
    
    def test_comment_count(self, Comment, test_task):
        """测试评论数统计"""
        pass
    
    def test_most_active_users(self, Activity, User):
        """测试最活跃用户"""
        pass
    
    def test_collaboration_metrics(self, Activity, Comment, test_project):
        """测试协作指标"""
        pass
    
    def test_response_time(self, Comment, test_task):
        """测试响应时间"""
        pass
    
    def test_engagement_rate(self, Activity, Comment, test_project):
        """测试参与度"""
        pass
```

### TestCollaborationSearch - 协作搜索测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestCollaborationSearch:
    """协作搜索测试"""
    
    def test_search_comments(self, Comment, test_project):
        """测试搜索评论"""
        pass
    
    def test_search_in_task_comments(self, Comment, test_task):
        """测试在任务评论中搜索"""
        pass
    
    def test_search_attachments(self, Attachment, test_project):
        """测试搜索附件"""
        pass
    
    def test_search_mentions(self, Mention, test_user):
        """测试搜索@提及"""
        pass
    
    def test_search_activity(self, Activity, test_project):
        """测试搜索活动"""
        pass
```

### TestCollaborationPerformance - 协作性能测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestCollaborationPerformance:
    """协作性能测试"""
    
    def test_comment_creation_speed(self, Comment, test_task, test_user):
        """测试评论创建速度"""
        pass
    
    def test_activity_feed_loading(self, Activity, test_project):
        """测试活动流加载"""
        pass
    
    def test_large_comment_thread(self, Comment, test_task):
        """测试大评论线程（100+评论）"""
        pass
    
    def test_notification_delivery(self, Notification, test_users):
        """测试通知送达速度"""
        pass
    
    def test_concurrent_commenting(self, Comment, test_task, test_users):
        """测试并发评论"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **任务评论**
   - 添加评论
   - 回复评论
   - 编辑/删除评论
   - 评论线程
   - Markdown支持
   - 评论历史

2. **@提及**
   - 评论中提及
   - 任务描述提及
   - 提及通知
   - 多个提及
   - 自动完成
   - 获取@我的内容

3. **文件附件**
   - 附加到任务/评论
   - 多文件附加
   - 文件验证
   - 下载附件
   - 移除附件
   - 附件预览
   - 版本管理

4. **活动动态**
   - 任务创建/更新
   - 评论活动
   - 分配变更
   - 项目活动流
   - 任务活动流
   - 用户活动流
   - 活动筛选

5. **实时更新**
   - 任务更新广播
   - 评论通知
   - 分配通知
   - 在线状态
   - 正在输入

6. **通知系统**
   - 任务分配通知
   - 评论通知
   - @提及通知
   - 截止日期通知
   - 通知偏好
   - 标记已读
   - 批量已读
   - 通知分组

7. **讨论线程**
   - 创建讨论
   - 参与者管理
   - 解决/重开讨论
   - 置顶讨论

8. **关注功能**
   - 关注任务/项目
   - 取消关注
   - 自动关注
   - 关注者通知

9. **协作权限**
   - 评论权限
   - 编辑权限
   - 管理员权限
   - 附件权限

10. **协作统计**
    - 评论数
    - 活跃用户
    - 协作指标
    - 响应时间
    - 参与度

11. **协作搜索**
    - 搜索评论
    - 任务评论搜索
    - 搜索附件
    - 搜索@提及
    - 搜索活动

12. **性能优化**
    - 评论创建速度
    - 活动流加载
    - 大评论线程
    - 通知送达
    - 并发评论

### 所需能力（Capabilities）

- **事务支持**：评论创建、通知发送的原子性
- **关系加载**：任务->评论->附件、评论->提及
- **聚合函数**：评论统计、活动统计
- **查询优化**：活动流查询、搜索功能

### 测试数据规模

- 用户：5-20 个用户
- 项目：3-10 个项目
- 任务：20-100 个任务
- 评论：每个任务 5-50 条评论
- 附件：30-50% 的评论带附件
- 活动记录：500-2000 条活动
- 通知：每个用户 50-200 条通知

### 性能预期

- 评论创建：< 100ms
- 评论加载（50条）：< 150ms
- 附件上传：< 500ms（取决于文件大小）
- 活动流加载（100条）：< 200ms
- 通知创建：< 50ms
- 通知列表：< 150ms（100条）
- @提及自动完成：< 100ms
- 大评论线程（100+）：< 500ms
- 并发评论（10用户）：< 200ms/用户
