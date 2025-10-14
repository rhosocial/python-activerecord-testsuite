# CMS系统 - 版本控制测试实施方案

## 测试目标

验证内容版本控制系统，包括修订跟踪、差异生成、版本回滚、分支管理、合并冲突处理和版本比较等功能。

## Provider 接口定义

### ICMSVersionControlProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ICMSVersionControlProvider(ABC):
    """CMS版本控制测试数据提供者接口"""
    
    @abstractmethod
    def setup_version_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Article
        Type[ActiveRecord],  # Revision
        Type[ActiveRecord],  # Branch
        Type[ActiveRecord],  # MergeRequest
        Type[ActiveRecord],  # Conflict
        Type[ActiveRecord]   # VersionMetadata
    ]:
        """设置版本控制相关模型"""
        pass
    
    @abstractmethod
    def create_article_with_history(
        self,
        article_id: int,
        revision_count: int
    ) -> Tuple[Dict, List[Dict]]:
        """创建带版本历史的文章"""
        pass
    
    @abstractmethod
    def create_branched_article(
        self,
        article_id: int,
        branch_count: int
    ) -> Tuple[Dict, List[Dict]]:
        """创建带分支的文章"""
        pass
    
    @abstractmethod
    def cleanup_version_data(self, scenario: str):
        """清理版本控制测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def version_models(request):
    """提供版本控制模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_cms_version_provider()
    
    models = provider.setup_version_models(scenario)
    yield models
    
    provider.cleanup_version_data(scenario)

@pytest.fixture
def User(version_models):
    """用户模型"""
    return version_models[0]

@pytest.fixture
def Article(version_models):
    """文章模型"""
    return version_models[1]

@pytest.fixture
def Revision(version_models):
    """修订版本模型"""
    return version_models[2]

@pytest.fixture
def Branch(version_models):
    """分支模型"""
    return version_models[3]

@pytest.fixture
def MergeRequest(version_models):
    """合并请求模型"""
    return version_models[4]

@pytest.fixture
def Conflict(version_models):
    """冲突模型"""
    return version_models[5]

@pytest.fixture
def VersionMetadata(version_models):
    """版本元数据模型"""
    return version_models[6]

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
def article_with_history(request, Article, Revision, test_author):
    """带版本历史的文章"""
    provider = get_cms_version_provider()
    article, revisions = provider.create_article_with_history(
        article_id=1,
        revision_count=10
    )
    return article, revisions
```

## 测试类和函数签名

### TestRevisionTracking - 修订跟踪测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestRevisionTracking:
    """修订跟踪测试"""
    
    def test_create_initial_revision(self, Article, Revision, test_author):
        """测试创建初始版本"""
        pass
    
    def test_create_revision_on_save(self, Article, Revision, test_author):
        """测试保存时创建新版本"""
        pass
    
    def test_revision_numbering(self, Article, Revision, test_author):
        """测试版本号编号"""
        pass
    
    def test_revision_author(self, Article, Revision, test_author, test_editor):
        """测试版本作者记录"""
        pass
    
    def test_revision_timestamp(self, Article, Revision, test_author):
        """测试版本时间戳"""
        pass
    
    def test_revision_message(self, Article, Revision, test_author):
        """测试版本提交信息"""
        pass
    
    def test_revision_content_snapshot(self, Article, Revision, test_author):
        """测试版本内容快照"""
        pass
```

### TestRevisionHistory - 版本历史测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestRevisionHistory:
    """版本历史测试"""
    
    def test_get_revision_list(self, Article, Revision, article_with_history):
        """测试获取版本列表"""
        pass
    
    def test_revision_pagination(self, Article, Revision, article_with_history):
        """测试版本分页"""
        pass
    
    def test_filter_revisions_by_author(self, Article, Revision, User):
        """测试按作者筛选版本"""
        pass
    
    def test_filter_revisions_by_date(self, Article, Revision):
        """测试按日期筛选版本"""
        pass
    
    def test_revision_timeline(self, Article, Revision, article_with_history):
        """测试版本时间线"""
        pass
```

### TestDiffGeneration - 差异生成测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestDiffGeneration:
    """差异生成测试"""
    
    def test_generate_text_diff(self, Revision, article_with_history):
        """测试生成文本差异"""
        pass
    
    def test_unified_diff_format(self, Revision, article_with_history):
        """测试统一差异格式"""
        pass
    
    def test_side_by_side_diff(self, Revision, article_with_history):
        """测试并排差异显示"""
        pass
    
    def test_word_level_diff(self, Revision):
        """测试词级别差异"""
        pass
    
    def test_diff_with_large_changes(self, Revision):
        """测试大量改动的差异"""
        pass
    
    def test_diff_statistics(self, Revision, article_with_history):
        """测试差异统计（增加/删除行数）"""
        pass
```

### TestVersionRollback - 版本回滚测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestVersionRollback:
    """版本回滚测试"""
    
    def test_rollback_to_previous_version(self, Article, Revision, test_author):
        """测试回滚到上一版本"""
        pass
    
    def test_rollback_to_specific_version(self, Article, Revision, article_with_history):
        """测试回滚到指定版本"""
        pass
    
    def test_rollback_creates_new_revision(self, Article, Revision, test_author):
        """测试回滚创建新版本"""
        pass
    
    def test_rollback_preserves_history(self, Article, Revision):
        """测试回滚保留历史"""
        pass
    
    def test_rollback_permission_check(self, Article, Revision, User):
        """测试回滚权限检查"""
        pass
    
    def test_partial_rollback(self, Article, Revision):
        """测试部分字段回滚"""
        pass
```

### TestVersionComparison - 版本比较测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestVersionComparison:
    """版本比较测试"""
    
    def test_compare_two_versions(self, Revision, article_with_history):
        """测试比较两个版本"""
        pass
    
    def test_compare_with_current(self, Article, Revision):
        """测试与当前版本比较"""
        pass
    
    def test_compare_non_adjacent_versions(self, Revision, article_with_history):
        """测试比较非相邻版本"""
        pass
    
    def test_highlight_changes(self, Revision):
        """测试高亮显示改动"""
        pass
    
    def test_metadata_comparison(self, Revision, VersionMetadata):
        """测试元数据比较"""
        pass
```

### TestBranchManagement - 分支管理测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestBranchManagement:
    """分支管理测试"""
    
    def test_create_branch(self, Article, Branch, test_author):
        """测试创建分支"""
        pass
    
    def test_branch_from_revision(self, Article, Branch, Revision, article_with_history):
        """测试从指定版本创建分支"""
        pass
    
    def test_list_branches(self, Branch, Article):
        """测试列出分支"""
        pass
    
    def test_switch_branch(self, Article, Branch, test_author):
        """测试切换分支"""
        pass
    
    def test_delete_branch(self, Branch, test_author):
        """测试删除分支"""
        pass
    
    def test_branch_isolation(self, Article, Branch, test_author):
        """测试分支隔离（互不影响）"""
        pass
```

### TestParallelEditing - 并行编辑测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestParallelEditing:
    """并行编辑测试"""
    
    def test_concurrent_edits_different_branches(self, Article, Branch, User):
        """测试不同分支并行编辑"""
        pass
    
    def test_concurrent_edits_same_branch(self, Article, Branch, User):
        """测试同一分支并行编辑"""
        pass
    
    def test_edit_conflict_detection(self, Article, User):
        """测试编辑冲突检测"""
        pass
    
    def test_optimistic_locking(self, Article, User):
        """测试乐观锁"""
        pass
```

### TestMergeOperation - 合并操作测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
@pytest.mark.workflow
class TestMergeOperation:
    """合并操作测试"""
    
    def test_merge_branch_to_main(self, Article, Branch, MergeRequest, test_author):
        """测试合并分支到主分支"""
        pass
    
    def test_merge_without_conflicts(self, Article, Branch, MergeRequest):
        """测试无冲突合并"""
        pass
    
    def test_fast_forward_merge(self, Branch, MergeRequest):
        """测试快进合并"""
        pass
    
    def test_three_way_merge(self, Branch, MergeRequest):
        """测试三方合并"""
        pass
    
    def test_merge_creates_merge_commit(self, Article, Branch, Revision):
        """测试合并创建合并提交"""
        pass
```

### TestConflictResolution - 冲突解决测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestConflictResolution:
    """冲突解决测试"""
    
    def test_detect_merge_conflict(self, Article, Branch, Conflict):
        """测试检测合并冲突"""
        pass
    
    def test_conflict_markers(self, Conflict):
        """测试冲突标记"""
        pass
    
    def test_manual_conflict_resolution(self, Article, Conflict, test_author):
        """测试手动解决冲突"""
        pass
    
    def test_accept_incoming_changes(self, Conflict, test_author):
        """测试接受传入改动"""
        pass
    
    def test_accept_current_changes(self, Conflict, test_author):
        """测试接受当前改动"""
        pass
    
    def test_accept_both_changes(self, Conflict, test_author):
        """测试接受双方改动"""
        pass
    
    def test_conflict_resolution_validation(self, Conflict):
        """测试冲突解决验证"""
        pass
```

### TestMergeRequest - 合并请求测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
@pytest.mark.workflow
class TestMergeRequest:
    """合并请求测试"""
    
    def test_create_merge_request(self, Branch, MergeRequest, test_author):
        """测试创建合并请求"""
        pass
    
    def test_merge_request_review(self, MergeRequest, test_editor):
        """测试合并请求审核"""
        pass
    
    def test_approve_merge_request(self, MergeRequest, test_editor):
        """测试批准合并请求"""
        pass
    
    def test_reject_merge_request(self, MergeRequest, test_editor):
        """测试拒绝合并请求"""
        pass
    
    def test_merge_request_discussion(self, MergeRequest, User):
        """测试合并请求讨论"""
        pass
    
    def test_merge_request_status(self, MergeRequest):
        """测试合并请求状态"""
        pass
```

### TestVersionMetadata - 版本元数据测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestVersionMetadata:
    """版本元数据测试"""
    
    def test_store_metadata(self, Revision, VersionMetadata, test_author):
        """测试存储版本元数据"""
        pass
    
    def test_metadata_tags(self, Revision, VersionMetadata):
        """测试元数据标签"""
        pass
    
    def test_metadata_search(self, VersionMetadata):
        """测试元数据搜索"""
        pass
    
    def test_custom_metadata_fields(self, VersionMetadata):
        """测试自定义元数据字段"""
        pass
```

### TestVersionStatistics - 版本统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_cms
class TestVersionStatistics:
    """版本统计测试"""
    
    def test_revision_count(self, Article, Revision):
        """测试版本数统计"""
        pass
    
    def test_contributor_statistics(self, Article, Revision, User):
        """测试贡献者统计"""
        pass
    
    def test_edit_frequency(self, Article, Revision):
        """测试编辑频率"""
        pass
    
    def test_version_size_statistics(self, Revision):
        """测试版本大小统计"""
        pass
    
    def test_branch_statistics(self, Branch):
        """测试分支统计"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **修订跟踪**
   - 初始版本创建
   - 自动版本创建
   - 版本编号
   - 作者记录
   - 时间戳
   - 提交信息
   - 内容快照

2. **版本历史**
   - 版本列表
   - 版本分页
   - 按作者筛选
   - 按日期筛选
   - 版本时间线

3. **差异生成**
   - 文本差异
   - 统一差异格式
   - 并排差异
   - 词级别差异
   - 大改动处理
   - 差异统计

4. **版本回滚**
   - 回滚到上一版本
   - 回滚到指定版本
   - 回滚创建新版本
   - 历史保留
   - 权限检查
   - 部分回滚

5. **版本比较**
   - 两版本比较
   - 与当前比较
   - 非相邻版本比较
   - 改动高亮
   - 元数据比较

6. **分支管理**
   - 分支创建
   - 从指定版本创建
   - 分支列表
   - 分支切换
   - 分支删除
   - 分支隔离

7. **并行编辑**
   - 不同分支并行
   - 同分支并行
   - 冲突检测
   - 乐观锁

8. **合并操作**
   - 分支合并
   - 无冲突合并
   - 快进合并
   - 三方合并
   - 合并提交

9. **冲突解决**
   - 冲突检测
   - 冲突标记
   - 手动解决
   - 接受传入/当前/双方改动
   - 解决验证

10. **合并请求**
    - 创建请求
    - 请求审核
    - 批准/拒绝
    - 讨论功能
    - 状态管理

11. **版本元数据**
    - 元数据存储
    - 标签管理
    - 元数据搜索
    - 自定义字段

12. **版本统计**
    - 版本数统计
    - 贡献者统计
    - 编辑频率
    - 版本大小
    - 分支统计

### 所需能力（Capabilities）

- **事务支持**：版本创建、合并操作的原子性
- **关系加载**：文章->版本历史的复杂关系
- **聚合函数**：版本统计、贡献者统计
- **查询构建**：版本筛选、差异查询

### 测试数据规模

- 文章：5-20 篇文章
- 版本：每篇文章 5-50 个版本
- 分支：每篇文章 1-5 个分支
- 合并请求：5-20 个请求
- 冲突：模拟 2-10 个冲突场景

### 性能预期

- 版本创建：< 50ms
- 版本列表查询：< 100ms（50个版本）
- 差异生成：< 200ms（中等改动）
- 版本回滚：< 100ms
- 分支创建：< 50ms
- 合并操作（无冲突）：< 300ms
- 冲突检测：< 100ms
- 版本比较：< 150ms
