# CMS系统 - 内容发布流程测试实施方案

## 测试目标

验证完整的内容发布流程，包括草稿创建、内容编辑、自动保存、媒体管理、分类标签管理、发布工作流、定时发布和内容预览等核心CMS功能。

## Provider 接口定义

### ICMSPublishingProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ICMSPublishingProvider(ABC):
    """CMS内容发布测试数据提供者接口"""
    
    @abstractmethod
    def setup_cms_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Article
        Type[ActiveRecord],  # Page
        Type[ActiveRecord],  # Category
        Type[ActiveRecord],  # Tag
        Type[ActiveRecord],  # Media
        Type[ActiveRecord],  # Draft
        Type[ActiveRecord]   # PublishSchedule
    ]:
        """设置CMS发布相关模型"""
        pass
    
    @abstractmethod
    def create_test_users(
        self,
        author_count: int,
        editor_count: int,
        admin_count: int
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """创建测试用户（作者、编辑、管理员）"""
        pass
    
    @abstractmethod
    def create_category_hierarchy(
        self,
        root_count: int,
        max_depth: int
    ) -> List[Dict]:
        """创建分类层次结构"""
        pass
    
    @abstractmethod
    def create_sample_tags(
        self,
        tag_count: int
    ) -> List[Dict]:
        """创建示例标签"""
        pass
    
    @abstractmethod
    def cleanup_cms_data(self, scenario: str):
        """清理CMS测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def cms_models(request):
    """提供CMS发布模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_cms_publishing_provider()
    
    models = provider.setup_cms_models(scenario)
    yield models
    
    provider.cleanup_cms_data(scenario)

@pytest.fixture
def User(cms_models):
    """用户模型"""
    return cms_models[0]

@pytest.fixture
def Article(cms_models):
    """文章模型"""
    return cms_models[1]

@pytest.fixture
def Page(cms_models):
    """页面模型"""
    return cms_models[2]

@pytest.fixture
def Category(cms_models):
    """分类模型"""
    return cms_models[3]

@pytest.fixture
def Tag(cms_models):
    """标签模型"""
    return cms_models[4]

@pytest.fixture
def Media(cms_models):
    """媒体模型"""
    return cms_models[5]

@pytest.fixture
def Draft(cms_models):
    """草稿模型"""
    return cms_models[6]

@pytest.fixture
def PublishSchedule(cms_models):
    """发布计划模型"""
    return cms_models[7]

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
def test_editor(User):
    """测试编辑"""
    editor = User(
        username="test_editor",
        email="editor@test.com",
        role="editor",
        is_active=True
    )
    editor.save()
    return editor

@pytest.fixture
def test_categories(request, Category):
    """测试分类层次"""
    provider = get_cms_publishing_provider()
    categories = provider.create_category_hierarchy(
        root_count=3,
        max_depth=3
    )
    return categories

@pytest.fixture
def test_tags(request, Tag):
    """测试标签"""
    provider = get_cms_publishing_provider()
    tags = provider.create_sample_tags(tag_count=20)
    return tags
```

## 测试类和函数签名

### TestDraftCreation - 草稿创建测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestDraftCreation:
    """草稿创建测试"""
    
    def test_create_article_draft(self, Article, Draft, test_author):
        """测试创建文章草稿"""
        pass
    
    def test_create_page_draft(self, Page, Draft, test_author):
        """测试创建页面草稿"""
        pass
    
    def test_draft_with_title_only(self, Article, Draft, test_author):
        """测试仅标题的草稿"""
        pass
    
    def test_draft_with_full_content(self, Article, Draft, test_author):
        """测试完整内容草稿"""
        pass
    
    def test_draft_validation(self, Article, Draft, test_author):
        """测试草稿内容验证"""
        pass
    
    def test_multiple_drafts_per_user(self, Article, Draft, test_author):
        """测试用户多个草稿"""
        pass
```

### TestContentEditing - 内容编辑测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestContentEditing:
    """内容编辑测试"""
    
    def test_edit_draft_content(self, Draft, test_author):
        """测试编辑草稿内容"""
        pass
    
    def test_edit_published_content(self, Article, test_author):
        """测试编辑已发布内容"""
        pass
    
    def test_concurrent_editing_prevention(self, Article, User):
        """测试防止并发编辑冲突"""
        pass
    
    def test_content_locking(self, Article, User):
        """测试内容锁定机制"""
        pass
    
    def test_edit_permission_check(self, Article, User):
        """测试编辑权限检查"""
        pass
```

### TestAutoSave - 自动保存测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestAutoSave:
    """自动保存测试"""
    
    def test_autosave_draft(self, Draft, test_author):
        """测试草稿自动保存"""
        pass
    
    def test_autosave_frequency(self, Draft, test_author):
        """测试自动保存频率"""
        pass
    
    def test_autosave_on_change(self, Draft, test_author):
        """测试内容变更时自动保存"""
        pass
    
    def test_recover_from_autosave(self, Draft, test_author):
        """测试从自动保存恢复"""
        pass
    
    def test_autosave_timestamp(self, Draft, test_author):
        """测试自动保存时间戳"""
        pass
```

### TestMediaManagement - 媒体管理测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestMediaManagement:
    """媒体管理测试"""
    
    def test_upload_image(self, Media, test_author):
        """测试上传图片"""
        pass
    
    def test_upload_file(self, Media, test_author):
        """测试上传文件"""
        pass
    
    def test_attach_media_to_article(self, Article, Media, test_author):
        """测试附加媒体到文章"""
        pass
    
    def test_media_validation(self, Media, test_author):
        """测试媒体验证（格式、大小）"""
        pass
    
    def test_remove_media(self, Article, Media, test_author):
        """测试移除媒体"""
        pass
    
    def test_media_library(self, Media, test_author):
        """测试媒体库管理"""
        pass
    
    def test_featured_image(self, Article, Media, test_author):
        """测试特色图片"""
        pass
```

### TestCategoryManagement - 分类管理测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
@requires_capabilities((CapabilityCategory.CTE, CTECapability.RECURSIVE_CTE))
class TestCategoryManagement:
    """分类管理测试"""
    
    def test_create_category(self, Category, test_author):
        """测试创建分类"""
        pass
    
    def test_create_subcategory(self, Category, test_author):
        """测试创建子分类"""
        pass
    
    def test_assign_category_to_article(self, Article, Category, test_author):
        """测试为文章分配分类"""
        pass
    
    def test_multiple_categories(self, Article, Category, test_author):
        """测试文章多分类"""
        pass
    
    def test_category_hierarchy_query(self, Category, test_categories):
        """测试分类层次查询"""
        pass
    
    def test_get_articles_by_category(self, Article, Category, test_author):
        """测试按分类获取文章"""
        pass
    
    def test_category_tree_navigation(self, Category, test_categories):
        """测试分类树导航"""
        pass
```

### TestTagManagement - 标签管理测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestTagManagement:
    """标签管理测试"""
    
    def test_create_tag(self, Tag, test_author):
        """测试创建标签"""
        pass
    
    def test_assign_tags_to_article(self, Article, Tag, test_author, test_tags):
        """测试为文章分配标签"""
        pass
    
    def test_tag_autocomplete(self, Tag, test_tags):
        """测试标签自动完成"""
        pass
    
    def test_popular_tags(self, Tag, Article, test_tags):
        """测试热门标签统计"""
        pass
    
    def test_get_articles_by_tag(self, Article, Tag, test_author, test_tags):
        """测试按标签获取文章"""
        pass
    
    def test_tag_cloud(self, Tag, Article, test_tags):
        """测试标签云数据"""
        pass
```

### TestContentPreview - 内容预览测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestContentPreview:
    """内容预览测试"""
    
    def test_preview_draft(self, Draft, test_author):
        """测试预览草稿"""
        pass
    
    def test_preview_with_template(self, Article, test_author):
        """测试使用模板预览"""
        pass
    
    def test_preview_url_generation(self, Article, test_author):
        """测试预览URL生成"""
        pass
    
    def test_preview_expiry(self, Article, test_author):
        """测试预览链接过期"""
        pass
    
    def test_preview_with_unpublished_content(self, Article, test_author):
        """测试预览未发布内容"""
        pass
```

### TestPublishingWorkflow - 发布工作流测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
@pytest.mark.workflow
class TestPublishingWorkflow:
    """发布工作流测试"""
    
    def test_publish_draft(self, Article, Draft, test_author):
        """测试发布草稿"""
        pass
    
    def test_submit_for_review(self, Article, Draft, test_author):
        """测试提交审核"""
        pass
    
    def test_approve_for_publishing(self, Article, test_author, test_editor):
        """测试审批发布"""
        pass
    
    def test_reject_publishing(self, Article, test_author, test_editor):
        """测试拒绝发布"""
        pass
    
    def test_unpublish_article(self, Article, test_author):
        """测试取消发布"""
        pass
    
    def test_workflow_status_transitions(self, Article, Draft, test_author):
        """测试工作流状态转换"""
        pass
    
    def test_workflow_notifications(self, Article, User, test_author, test_editor):
        """测试工作流通知"""
        pass
```

### TestScheduledPublishing - 定时发布测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestScheduledPublishing:
    """定时发布测试"""
    
    def test_schedule_publish_date(self, Article, PublishSchedule, test_author):
        """测试设置发布日期"""
        pass
    
    def test_schedule_future_publish(self, Article, PublishSchedule, test_author):
        """测试未来发布计划"""
        pass
    
    def test_schedule_unpublish(self, Article, PublishSchedule, test_author):
        """测试定时取消发布"""
        pass
    
    def test_modify_schedule(self, PublishSchedule, test_author):
        """测试修改发布计划"""
        pass
    
    def test_cancel_schedule(self, PublishSchedule, test_author):
        """测试取消发布计划"""
        pass
    
    def test_execute_scheduled_publish(self, Article, PublishSchedule):
        """测试执行定时发布"""
        pass
    
    def test_schedule_queue(self, PublishSchedule):
        """测试发布计划队列"""
        pass
```

### TestContentStatus - 内容状态测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestContentStatus:
    """内容状态管理测试"""
    
    def test_status_draft(self, Article, test_author):
        """测试草稿状态"""
        pass
    
    def test_status_pending_review(self, Article, test_author):
        """测试待审核状态"""
        pass
    
    def test_status_published(self, Article, test_author):
        """测试已发布状态"""
        pass
    
    def test_status_archived(self, Article, test_author):
        """测试归档状态"""
        pass
    
    def test_status_history(self, Article, test_author):
        """测试状态历史跟踪"""
        pass
    
    def test_filter_by_status(self, Article, test_author):
        """测试按状态筛选内容"""
        pass
```

### TestContentMetadata - 内容元数据测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestContentMetadata:
    """内容元数据测试"""
    
    def test_set_seo_title(self, Article, test_author):
        """测试设置SEO标题"""
        pass
    
    def test_set_meta_description(self, Article, test_author):
        """测试设置元描述"""
        pass
    
    def test_set_keywords(self, Article, test_author):
        """测试设置关键词"""
        pass
    
    def test_set_canonical_url(self, Article, test_author):
        """测试设置规范URL"""
        pass
    
    def test_social_media_metadata(self, Article, test_author):
        """测试社交媒体元数据（Open Graph, Twitter Card）"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **草稿管理**
   - 创建文章/页面草稿
   - 草稿内容验证
   - 多草稿管理
   - 草稿保存

2. **内容编辑**
   - 内容编辑
   - 并发编辑防护
   - 内容锁定
   - 权限检查

3. **自动保存**
   - 定时自动保存
   - 变更触发保存
   - 自动保存恢复
   - 时间戳跟踪

4. **媒体管理**
   - 图片/文件上传
   - 媒体附加
   - 媒体验证
   - 媒体库管理
   - 特色图片

5. **分类管理**
   - 分类创建
   - 分类层次
   - 分类分配
   - 多分类支持
   - 分类查询（需要CTE）

6. **标签管理**
   - 标签创建
   - 标签分配
   - 标签自动完成
   - 热门标签
   - 标签云

7. **内容预览**
   - 草稿预览
   - 模板预览
   - 预览URL
   - 预览过期

8. **发布工作流**
   - 草稿发布
   - 提交审核
   - 审批/拒绝
   - 取消发布
   - 状态转换
   - 通知系统

9. **定时发布**
   - 发布计划
   - 未来发布
   - 定时取消发布
   - 计划修改/取消
   - 计划执行
   - 发布队列

10. **状态管理**
    - 多种状态（草稿、审核中、已发布、归档）
    - 状态历史
    - 状态筛选

11. **元数据**
    - SEO优化（标题、描述、关键词）
    - 规范URL
    - 社交媒体元数据

### 所需能力（Capabilities）

- **CTE支持**：分类层次查询需要递归CTE
- **事务支持**：发布流程的多步骤原子性
- **关系加载**：文章->分类、文章->标签、文章->媒体
- **聚合函数**：标签统计、分类文章数
- **查询构建**：复杂的内容筛选、搜索

### 测试数据规模

- 用户：3-10 个作者，1-3 个编辑，1 个管理员
- 文章：20-100 篇文章
- 分类：10-30 个分类，层次深度 2-4
- 标签：20-50 个标签
- 媒体：30-100 个媒体文件
- 草稿：每个作者 2-5 个草稿

### 性能预期

- 草稿创建/保存：< 50ms
- 自动保存：< 30ms
- 媒体上传：< 500ms（取决于文件大小）
- 分类树查询：< 100ms（深度4）
- 内容发布：< 200ms（包含工作流）
- 预览生成：< 100ms
- 定时发布执行：< 100ms/篇文章
