# 社交网络 - 消息系统测试实施方案

## 测试目标

验证私信消息系统，包括直接消息发送、对话线程管理、已读回执、消息搜索、批量操作和消息通知等功能。

## Provider 接口定义

### ISocialMessagingProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ISocialMessagingProvider(ABC):
    """社交消息系统测试数据提供者接口"""
    
    @abstractmethod
    def setup_messaging_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Message
        Type[ActiveRecord],  # Conversation
        Type[ActiveRecord],  # ConversationParticipant
        Type[ActiveRecord],  # MessageRead
        Type[ActiveRecord],  # MessageAttachment
        Type[ActiveRecord]   # MessageNotification
    ]:
        """设置消息系统相关模型"""
        pass
    
    @abstractmethod
    def create_conversations(
        self,
        user_count: int,
        conversations_per_user: int
    ) -> List[Dict]:
        """创建对话数据"""
        pass
    
    @abstractmethod
    def create_messages(
        self,
        conversation_count: int,
        messages_per_conversation_range: Tuple[int, int]
    ) -> List[Dict]:
        """创建消息数据"""
        pass
    
    @abstractmethod
    def cleanup_messaging_data(self, scenario: str):
        """清理消息测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def messaging_models(request):
    """提供消息系统模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_social_messaging_provider()
    
    models = provider.setup_messaging_models(scenario)
    yield models
    
    provider.cleanup_messaging_data(scenario)

@pytest.fixture
def User(messaging_models):
    """用户模型"""
    return messaging_models[0]

@pytest.fixture
def Message(messaging_models):
    """消息模型"""
    return messaging_models[1]

@pytest.fixture
def Conversation(messaging_models):
    """对话模型"""
    return messaging_models[2]

@pytest.fixture
def ConversationParticipant(messaging_models):
    """对话参与者模型"""
    return messaging_models[3]

@pytest.fixture
def MessageRead(messaging_models):
    """消息已读模型"""
    return messaging_models[4]

@pytest.fixture
def MessageAttachment(messaging_models):
    """消息附件模型"""
    return messaging_models[5]

@pytest.fixture
def MessageNotification(messaging_models):
    """消息通知模型"""
    return messaging_models[6]

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
def test_recipient(User):
    """测试接收者"""
    user = User(
        username="test_recipient",
        email="recipient@test.com",
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
def test_conversations(request, Conversation, test_user, test_users):
    """测试对话数据"""
    provider = get_social_messaging_provider()
    conversations = provider.create_conversations(
        user_count=10,
        conversations_per_user=5
    )
    return conversations
```

## 测试类和函数签名

### TestDirectMessaging - 直接消息测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestDirectMessaging:
    """直接消息测试"""
    
    def test_send_message(self, Message, Conversation, test_user, test_recipient):
        """测试发送消息"""
        pass
    
    def test_send_message_to_multiple_users(self, Message, Conversation, test_user, test_users):
        """测试发送消息给多个用户（群聊）"""
        pass
    
    def test_receive_message(self, Message, Conversation, test_user, test_recipient):
        """测试接收消息"""
        pass
    
    def test_message_validation(self, Message, test_user, test_recipient):
        """测试消息内容验证"""
        pass
    
    def test_empty_message_prevention(self, Message, test_user, test_recipient):
        """测试防止空消息"""
        pass
    
    def test_message_length_limit(self, Message, test_user, test_recipient):
        """测试消息长度限制"""
        pass
```

### TestConversationThreads - 对话线程测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestConversationThreads:
    """对话线程测试"""
    
    def test_create_conversation(self, Conversation, ConversationParticipant, test_user, test_recipient):
        """测试创建对话"""
        pass
    
    def test_get_conversation_history(self, Message, Conversation, test_user):
        """测试获取对话历史"""
        pass
    
    def test_conversation_participants(self, Conversation, ConversationParticipant, test_users):
        """测试对话参与者"""
        pass
    
    def test_add_participant(self, Conversation, ConversationParticipant, test_user, test_users):
        """测试添加参与者"""
        pass
    
    def test_remove_participant(self, Conversation, ConversationParticipant, test_users):
        """测试移除参与者"""
        pass
    
    def test_leave_conversation(self, Conversation, ConversationParticipant, test_user):
        """测试离开对话"""
        pass
    
    def test_conversation_list(self, Conversation, test_user):
        """测试对话列表"""
        pass
```

### TestMessageRead - 已读回执测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageRead:
    """已读回执测试"""
    
    def test_mark_message_as_read(self, Message, MessageRead, test_recipient):
        """测试标记消息为已读"""
        pass
    
    def test_read_receipt_timestamp(self, Message, MessageRead, test_recipient):
        """测试已读时间戳"""
        pass
    
    def test_unread_message_count(self, Message, MessageRead, test_user):
        """测试未读消息数"""
        pass
    
    def test_conversation_unread_count(self, Conversation, Message, MessageRead, test_user):
        """测试对话未读数"""
        pass
    
    def test_mark_conversation_as_read(self, Conversation, Message, MessageRead, test_user):
        """测试标记整个对话为已读"""
        pass
    
    def test_read_by_multiple_users(self, Message, MessageRead, test_users):
        """测试多用户已读状态"""
        pass
    
    def test_delivery_status(self, Message, test_recipient):
        """测试消息送达状态"""
        pass
```

### TestMessageSearch - 消息搜索测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageSearch:
    """消息搜索测试"""
    
    def test_search_messages_by_keyword(self, Message, test_user):
        """测试按关键词搜索消息"""
        pass
    
    def test_search_in_conversation(self, Message, Conversation, test_user):
        """测试在对话中搜索"""
        pass
    
    def test_search_by_sender(self, Message, User, test_user):
        """测试按发送者搜索"""
        pass
    
    def test_search_by_date_range(self, Message, test_user):
        """测试按日期范围搜索"""
        pass
    
    def test_search_with_filters(self, Message, test_user):
        """测试带过滤器搜索"""
        pass
    
    def test_search_result_highlighting(self, Message, test_user):
        """测试搜索结果高亮"""
        pass
```

### TestMessageAttachments - 消息附件测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageAttachments:
    """消息附件测试"""
    
    def test_send_image_attachment(self, Message, MessageAttachment, test_user, test_recipient):
        """测试发送图片附件"""
        pass
    
    def test_send_file_attachment(self, Message, MessageAttachment, test_user, test_recipient):
        """测试发送文件附件"""
        pass
    
    def test_multiple_attachments(self, Message, MessageAttachment, test_user, test_recipient):
        """测试多个附件"""
        pass
    
    def test_attachment_validation(self, MessageAttachment, test_user):
        """测试附件验证（格式、大小）"""
        pass
    
    def test_download_attachment(self, MessageAttachment, test_recipient):
        """测试下载附件"""
        pass
    
    def test_attachment_preview(self, MessageAttachment, test_recipient):
        """测试附件预览"""
        pass
```

### TestBulkOperations - 批量操作测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestBulkOperations:
    """批量操作测试"""
    
    def test_mark_multiple_as_read(self, Message, MessageRead, test_user):
        """测试批量标记为已读"""
        pass
    
    def test_delete_multiple_messages(self, Message, test_user):
        """测试批量删除消息"""
        pass
    
    def test_archive_conversations(self, Conversation, test_user):
        """测试归档对话"""
        pass
    
    def test_unarchive_conversations(self, Conversation, test_user):
        """测试取消归档"""
        pass
    
    def test_mute_conversation(self, Conversation, test_user):
        """测试静音对话"""
        pass
    
    def test_unmute_conversation(self, Conversation, test_user):
        """测试取消静音"""
        pass
    
    def test_bulk_operation_performance(self, Message, test_user):
        """测试批量操作性能"""
        pass
```

### TestMessageNotifications - 消息通知测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageNotifications:
    """消息通知测试"""
    
    def test_notify_on_new_message(self, Message, MessageNotification, test_recipient):
        """测试新消息通知"""
        pass
    
    def test_notification_preferences(self, User, MessageNotification, test_user):
        """测试通知偏好设置"""
        pass
    
    def test_muted_conversation_notifications(self, Conversation, Message, MessageNotification):
        """测试静音对话的通知"""
        pass
    
    def test_notification_badge_count(self, Message, MessageNotification, test_user):
        """测试通知角标计数"""
        pass
    
    def test_clear_notifications(self, MessageNotification, test_user):
        """测试清除通知"""
        pass
    
    def test_push_notifications(self, Message, MessageNotification):
        """测试推送通知（如支持）"""
        pass
```

### TestMessageDeletion - 消息删除测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageDeletion:
    """消息删除测试"""
    
    def test_delete_message_for_self(self, Message, test_user):
        """测试为自己删除消息"""
        pass
    
    def test_delete_message_for_everyone(self, Message, test_user):
        """测试为所有人删除消息"""
        pass
    
    def test_delete_time_limit(self, Message, test_user):
        """测试删除时间限制"""
        pass
    
    def test_deletion_notification(self, Message, test_recipient):
        """测试删除通知"""
        pass
    
    def test_delete_conversation(self, Conversation, Message, test_user):
        """测试删除整个对话"""
        pass
```

### TestGroupMessaging - 群组消息测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestGroupMessaging:
    """群组消息测试"""
    
    def test_create_group_conversation(self, Conversation, ConversationParticipant, test_users):
        """测试创建群组对话"""
        pass
    
    def test_send_group_message(self, Message, Conversation, test_user, test_users):
        """测试发送群组消息"""
        pass
    
    def test_group_message_delivery(self, Message, Conversation, test_users):
        """测试群组消息送达"""
        pass
    
    def test_add_member_to_group(self, Conversation, ConversationParticipant, test_users):
        """测试添加群组成员"""
        pass
    
    def test_remove_member_from_group(self, Conversation, ConversationParticipant, test_users):
        """测试移除群组成员"""
        pass
    
    def test_group_admin_permissions(self, Conversation, ConversationParticipant, test_users):
        """测试群组管理员权限"""
        pass
    
    def test_leave_group(self, Conversation, ConversationParticipant, test_user):
        """测试离开群组"""
        pass
```

### TestMessageThreading - 消息线程测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageThreading:
    """消息线程测试"""
    
    def test_reply_to_message(self, Message, test_user, test_recipient):
        """测试回复消息"""
        pass
    
    def test_thread_view(self, Message, Conversation):
        """测试线程视图"""
        pass
    
    def test_nested_replies(self, Message, test_users):
        """测试嵌套回复"""
        pass
    
    def test_thread_participants(self, Message, test_users):
        """测试线程参与者"""
        pass
```

### TestMessageSynchronization - 消息同步测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageSynchronization:
    """消息同步测试"""
    
    def test_sync_across_devices(self, Message, test_user):
        """测试跨设备同步"""
        pass
    
    def test_offline_message_queue(self, Message, test_recipient):
        """测试离线消息队列"""
        pass
    
    def test_message_order_consistency(self, Message, Conversation):
        """测试消息顺序一致性"""
        pass
    
    def test_sync_read_status(self, Message, MessageRead, test_user):
        """测试已读状态同步"""
        pass
```

### TestMessageStatistics - 消息统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessageStatistics:
    """消息统计测试"""
    
    def test_total_message_count(self, Message, test_user):
        """测试消息总数"""
        pass
    
    def test_messages_by_conversation(self, Message, Conversation):
        """测试按对话统计消息"""
        pass
    
    def test_average_response_time(self, Message, Conversation):
        """测试平均回复时间"""
        pass
    
    def test_most_active_conversations(self, Conversation, Message, test_user):
        """测试最活跃对话"""
        pass
    
    def test_messaging_activity_over_time(self, Message):
        """测试消息活动趋势"""
        pass
```

### TestMessagePerformance - 消息性能测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_social
class TestMessagePerformance:
    """消息性能测试"""
    
    def test_message_send_latency(self, Message, test_user, test_recipient):
        """测试消息发送延迟"""
        pass
    
    def test_conversation_load_performance(self, Conversation, Message):
        """测试对话加载性能"""
        pass
    
    def test_large_conversation_handling(self, Message, Conversation):
        """测试大对话处理（1000+消息）"""
        pass
    
    def test_concurrent_messaging(self, Message, test_users):
        """测试并发消息"""
        pass
    
    def test_search_performance(self, Message, test_user):
        """测试搜索性能"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **直接消息**
   - 发送消息
   - 多用户消息（群聊）
   - 接收消息
   - 内容验证
   - 空消息防止
   - 长度限制

2. **对话线程**
   - 创建对话
   - 对话历史
   - 参与者管理
   - 添加/移除参与者
   - 离开对话
   - 对话列表

3. **已读回执**
   - 标记已读
   - 已读时间戳
   - 未读计数
   - 对话未读数
   - 批量已读
   - 多用户已读
   - 送达状态

4. **消息搜索**
   - 关键词搜索
   - 对话内搜索
   - 按发送者搜索
   - 日期范围搜索
   - 过滤器
   - 结果高亮

5. **消息附件**
   - 图片附件
   - 文件附件
   - 多附件
   - 附件验证
   - 附件下载
   - 附件预览

6. **批量操作**
   - 批量已读
   - 批量删除
   - 归档/取消归档
   - 静音/取消静音
   - 性能优化

7. **消息通知**
   - 新消息通知
   - 通知偏好
   - 静音对话
   - 角标计数
   - 清除通知
   - 推送通知

8. **消息删除**
   - 为自己删除
   - 为所有人删除
   - 删除时限
   - 删除通知
   - 删除对话

9. **群组消息**
   - 创建群组
   - 群组消息
   - 消息送达
   - 成员管理
   - 管理员权限
   - 离开群组

10. **消息线程**
    - 回复消息
    - 线程视图
    - 嵌套回复
    - 线程参与者

11. **消息同步**
    - 跨设备同步
    - 离线队列
    - 顺序一致性
    - 已读同步

12. **消息统计**
    - 消息总数
    - 按对话统计
    - 回复时间
    - 活跃对话
    - 活动趋势

13. **性能优化**
    - 发送延迟
    - 加载性能
    - 大对话处理
    - 并发消息
    - 搜索性能

### 所需能力（Capabilities）

- **事务支持**：消息发送、群组操作的原子性
- **关系加载**：对话->消息、消息->附件、消息->已读状态
- **批量操作**：批量标记已读、批量删除
- **聚合函数**：未读计数、消息统计
- **查询优化**：消息搜索、对话加载性能

### 测试数据规模

- 用户：10-50 个用户
- 对话：每个用户 5-20 个对话
- 消息：每个对话 10-100 条消息
- 群组对话：5-10 个群组，每组 3-10 人
- 附件：20-30% 的消息带附件

### 性能预期

- 消息发送：< 100ms
- 对话列表加载：< 150ms
- 对话历史加载（50条）：< 200ms
- 标记已读：< 30ms
- 消息搜索：< 300ms
- 批量操作（100条）：< 500ms
- 群组消息送达：< 200ms
- 大对话（1000+消息）加载：< 1s
