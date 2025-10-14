# 关系加载基准：预加载测试实施方案

## 1. 测试目标

本测试套件深入测试 ActiveRecord 的预加载（Eager Loading）机制，评估不同预加载策略的性能和适用场景。预加载是解决 N+1 问题的关键技术。

**核心验证点：**
- 单关系预加载性能
- 多关系预加载性能
- 嵌套关系预加载性能
- 大结果集预加载的内存影响
- 不同预加载策略的对比
- 复杂关系图的加载优化

**业务价值：**
- 验证预加载机制的正确性
- 评估不同策略的性能
- 为开发者提供最佳实践
- 识别性能瓶颈

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict, Any
from rhosocial.activerecord import ActiveRecord

class IEagerLoadingBenchmarkProvider(ABC):
    """预加载基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_eager_loading_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # Organization
        Type[ActiveRecord],  # Team
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Project
        Type[ActiveRecord],  # Task
        Type[ActiveRecord],  # Comment
        Type[ActiveRecord]   # Attachment
    ]:
        """
        设置预加载测试模型（复杂关系图）。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 7 个模型类的元组：
            - Organization: 组织（has_many teams）
            - Team: 团队（belongs_to organization, has_many users, has_many projects）
            - User: 用户（belongs_to team, has_many tasks, has_many comments）
            - Project: 项目（belongs_to team, has_many tasks）
            - Task: 任务（belongs_to project, belongs_to user, has_many comments, has_many attachments）
            - Comment: 评论（belongs_to user, belongs_to task）
            - Attachment: 附件（belongs_to task）
        """
        pass
    
    @abstractmethod
    def populate_eager_loading_data(
        self,
        organizations: int = 5,
        teams_per_org: int = 3,
        users_per_team: int = 5,
        projects_per_team: int = 4,
        tasks_per_project: int = 10,
        comments_per_task: int = 3,
        attachments_per_task: int = 2
    ) -> Dict[str, Any]:
        """
        填充复杂关系的测试数据。
        
        Returns:
            包含统计信息的字典
        """
        pass
    
    @abstractmethod
    def get_query_counter(self) -> 'QueryCounter':
        """获取查询计数器。"""
        pass
    
    @abstractmethod
    def get_memory_profiler(self) -> 'MemoryProfiler':
        """获取内存分析器。"""
        pass
    
    @abstractmethod
    def cleanup_eager_loading_data(self, scenario: str):
        """清理预加载测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Tuple, Type, Dict, Any
import time
import tracemalloc
from rhosocial.activerecord import ActiveRecord

class MemoryProfiler:
    """内存分析器，跟踪内存使用。"""
    
    def __init__(self):
        self.start_memory = 0
        self.peak_memory = 0
        self.current_memory = 0
    
    def start(self):
        """开始内存监控。"""
        tracemalloc.start()
        self.start_memory = tracemalloc.get_traced_memory()[0]
    
    def stop(self):
        """停止内存监控。"""
        current, peak = tracemalloc.get_traced_memory()
        self.current_memory = current
        self.peak_memory = peak
        tracemalloc.stop()
    
    def get_usage(self) -> Dict[str, int]:
        """获取内存使用情况（字节）。"""
        return {
            'current': self.current_memory,
            'peak': self.peak_memory,
            'used': self.current_memory - self.start_memory
        }


@pytest.fixture
def eager_models(request) -> Tuple[
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord]
]:
    """
    提供预加载测试模型。
    
    Returns:
        (Organization, Team, User, Project, Task, Comment, Attachment)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("eager_loading_benchmark_provider")
    
    models = provider.setup_eager_loading_models(scenario)
    
    yield models
    
    provider.cleanup_eager_loading_data(scenario)


@pytest.fixture
def eager_test_data(eager_models, request):
    """填充预加载测试数据。"""
    provider = request.getfixturevalue("eager_loading_benchmark_provider")
    
    markers = [m.name for m in request.node.iter_markers()]
    
    if 'small_scale' in markers:
        stats = provider.populate_eager_loading_data(
            organizations=2,
            teams_per_org=2,
            users_per_team=3,
            projects_per_team=2,
            tasks_per_project=5,
            comments_per_task=2,
            attachments_per_task=1
        )
    elif 'medium_scale' in markers:
        stats = provider.populate_eager_loading_data(
            organizations=5,
            teams_per_org=4,
            users_per_team=8,
            projects_per_team=5,
            tasks_per_project=15,
            comments_per_task=4,
            attachments_per_task=2
        )
    elif 'large_scale' in markers:
        stats = provider.populate_eager_loading_data(
            organizations=10,
            teams_per_org=10,
            users_per_team=20,
            projects_per_team=10,
            tasks_per_project=30,
            comments_per_task=8,
            attachments_per_task=4
        )
    else:
        stats = provider.populate_eager_loading_data()
    
    yield stats


@pytest.fixture
def query_counter(request):
    """提供查询计数器。"""
    provider = request.getfixturevalue("eager_loading_benchmark_provider")
    counter = provider.get_query_counter()
    
    yield counter
    
    counter.stop()
    counter.reset()


@pytest.fixture
def memory_profiler(request):
    """提供内存分析器。"""
    provider = request.getfixturevalue("eager_loading_benchmark_provider")
    profiler = provider.get_memory_profiler()
    
    yield profiler
```

---

## 4. 测试类和函数签名

### 4.1 单关系预加载

```python
import pytest
import time

@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestSingleRelationEagerLoading:
    """测试单关系预加载性能。"""
    
    def test_belongs_to_eager_loading(
        self,
        eager_models,
        eager_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试 belongs_to 关系预加载。
        
        验证点：
        1. 使用 with_('parent') 预加载
        2. 验证查询数（应为2次）
        3. 测量加载时间
        4. 测量内存使用
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        # 预加载
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        tasks = Task.with_('project').all()
        # 访问关系数据
        for task in tasks:
            _ = task.project.name
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        # 验证
        assert query_counter.get_count() == 2
        
        print(f"Query count: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
        print(f"Memory: {memory_profiler.get_usage()['used'] / 1024 / 1024:.2f} MB")
    
    def test_has_many_eager_loading(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试 has_many 关系预加载。
        
        验证点：
        1. with_('tasks') 预加载多个子记录
        2. 验证查询数
        3. 正确性：所有任务都已加载
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        query_counter.start()
        start_time = time.time()
        
        projects = Project.with_('tasks').all()
        task_counts = []
        for project in projects:
            task_counts.append(len(project.tasks))
        
        end_time = time.time()
        query_counter.stop()
        
        assert query_counter.get_count() == 2
        print(f"Loaded {sum(task_counts)} tasks in {end_time - start_time:.4f}s")
    
    def test_has_one_eager_loading(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试 has_one 关系预加载（如果模型支持）。
        
        验证点：
        1. 单个关联对象的预加载
        2. 查询优化
        """
        # 实现类似测试
        pass


### 4.2 多关系预加载

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestMultipleRelationEagerLoading:
    """测试多关系预加载性能。"""
    
    def test_multiple_independent_relations(
        self,
        eager_models,
        eager_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试加载多个独立关系。
        
        验证点：
        1. with_('project', 'user', 'comments', 'attachments')
        2. 查询数应为 5 (1 + 4)
        3. 与分别加载相比的性能
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        tasks = Task.with_('project', 'user', 'comments', 'attachments').all()
        
        for task in tasks:
            _ = task.project.name
            _ = task.user.username
            _ = len(task.comments)
            _ = len(task.attachments)
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        # 验证查询数
        assert query_counter.get_count() == 5
        
        print(f"Multiple relations loaded with {query_counter.get_count()} queries")
        print(f"Time: {end_time - start_time:.4f}s")
        print(f"Memory: {memory_profiler.get_usage()['used'] / 1024 / 1024:.2f} MB")
    
    def test_selective_eager_loading(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试选择性预加载。
        
        验证点：
        1. 只加载需要的关系
        2. 避免过度预加载
        3. 查询数与加载关系数的关系
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        # 场景1：只需要 project
        query_counter.start()
        tasks = Task.with_('project').all()
        query_count_1 = query_counter.get_count()
        query_counter.reset()
        
        # 场景2：需要 project 和 user
        query_counter.start()
        tasks = Task.with_('project', 'user').all()
        query_count_2 = query_counter.get_count()
        query_counter.reset()
        
        # 场景3：需要所有关系
        query_counter.start()
        tasks = Task.with_('project', 'user', 'comments', 'attachments').all()
        query_count_3 = query_counter.get_count()
        
        # 验证查询数递增
        assert query_count_1 == 2
        assert query_count_2 == 3
        assert query_count_3 == 5


### 4.3 嵌套关系预加载

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.medium_scale
class TestNestedEagerLoading:
    """测试嵌套关系预加载性能。"""
    
    def test_two_level_nesting(
        self,
        eager_models,
        eager_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试两层嵌套预加载。
        
        验证点：
        1. Organization -> Teams -> Users
        2. with_('teams.users')
        3. 查询数应为 3
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        orgs = Organization.with_('teams.users').all()
        
        user_count = 0
        for org in orgs:
            for team in org.teams:
                user_count += len(team.users)
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        assert query_counter.get_count() == 3
        print(f"Loaded {user_count} users across organizations")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
    
    def test_three_level_nesting(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试三层嵌套预加载。
        
        验证点：
        1. Organization -> Teams -> Projects -> Tasks
        2. with_('teams.projects.tasks')
        3. 查询数应为 4
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        query_counter.start()
        start_time = time.time()
        
        orgs = Organization.with_('teams.projects.tasks').all()
        
        task_count = 0
        for org in orgs:
            for team in org.teams:
                for project in team.projects:
                    task_count += len(project.tasks)
        
        end_time = time.time()
        query_counter.stop()
        
        assert query_counter.get_count() == 4
        print(f"3-level nesting: {task_count} tasks loaded")
    
    def test_complex_nested_relations(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试复杂嵌套关系。
        
        验证点：
        1. Task -> (Project, User, Comments.User, Attachments)
        2. 混合多个嵌套路径
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        query_counter.start()
        
        tasks = Task.with_('project', 'user', 'comments.user', 'attachments').all()
        
        for task in tasks:
            _ = task.project.name
            _ = task.user.username
            for comment in task.comments:
                _ = comment.user.username
            _ = len(task.attachments)
        
        query_counter.stop()
        
        # 验证查询数
        # 1 (tasks) + 1 (projects) + 1 (users) + 1 (comments) + 1 (comment users) + 1 (attachments)
        assert query_counter.get_count() == 6


### 4.4 大结果集预加载

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.large_scale
class TestLargeResultSetEagerLoading:
    """测试大结果集的预加载性能和内存影响。"""
    
    def test_large_has_many_loading(
        self,
        eager_models,
        eager_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试加载大量子记录。
        
        验证点：
        1. 每个 Project 有很多 Tasks
        2. 内存使用情况
        3. 加载时间
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        projects = Project.with_('tasks').all()
        
        total_tasks = sum(len(p.tasks) for p in projects)
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        memory_used_mb = memory_profiler.get_usage()['used'] / 1024 / 1024
        
        print(f"Loaded {total_tasks} tasks")
        print(f"Time: {end_time - start_time:.4f}s")
        print(f"Memory: {memory_used_mb:.2f} MB")
        print(f"Memory per task: {memory_used_mb * 1024 / total_tasks:.2f} KB")
    
    def test_memory_vs_query_tradeoff(
        self,
        eager_models,
        eager_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试内存与查询数的权衡。
        
        验证点：
        1. 预加载使用更多内存但查询更少
        2. 懒加载使用更少内存但查询更多
        3. 找到平衡点
        """
        Organization, Team, User, Project, Task, Comment, Attachment = eager_models
        
        # 懒加载
        memory_profiler.start()
        query_counter.start()
        lazy_start = time.time()
        
        tasks = Task.all()
        for task in tasks[:100]:  # 只访问前100个
            _ = task.project.name
        
        lazy_time = time.time() - lazy_start
        lazy_queries = query_counter.get_count()
        lazy_memory = memory_profiler.get_usage()['used']
        memory_profiler.stop()
        query_counter.reset()
        
        # 预加载
        memory_profiler.start()
        query_counter.start()
        eager_start = time.time()
        
        tasks = Task.with_('project').all()  # 预加载全部
        for task in tasks[:100]:  # 访问前100个
            _ = task.project.name
        
        eager_time = time.time() - eager_start
        eager_queries = query_counter.get_count()
        eager_memory = memory_profiler.get_usage()['used']
        memory_profiler.stop()
        
        print(f"Lazy:  {lazy_queries} queries, {lazy_memory / 1024 / 1024:.2f} MB, {lazy_time:.4f}s")
        print(f"Eager: {eager_queries} queries, {eager_memory / 1024 / 1024:.2f} MB, {eager_time:.4f}s")


### 4.5 预加载策略对比

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.medium_scale
class TestEagerLoadingStrategies:
    """测试不同预加载策略的性能对比。"""
    
    def test_join_vs_separate_queries(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试 JOIN 查询 vs 分离查询策略。
        
        验证点：
        1. 某些 ORM 使用 JOIN 预加载
        2. 某些使用分离的 SELECT 查询
        3. 对比两种策略的性能
        """
        # 这取决于具体实现
        # 测试 ActiveRecord 的实际策略
        pass
    
    def test_batch_size_optimization(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试批量大小优化。
        
        验证点：
        1. 如果支持批量预加载
        2. 不同批量大小的影响
        3. 找到最优批量大小
        """
        # 如果支持批量预加载
        pass
    
    def test_preload_vs_includes(
        self,
        eager_models,
        eager_test_data,
        query_counter
    ):
        """
        测试不同预加载方法（如果有多种）。
        
        验证点：
        1. preload: 分离查询
        2. includes: JOIN 查询
        3. 性能对比
        """
        # 根据 ActiveRecord 实现调整
        pass
```

---

## 5. 性能基准目标

### 5.1 查询效率
- **单关系**: 2 queries (baseline + relation)
- **多关系**: 1 + N queries (N = 关系数)
- **嵌套关系**: 深度 + 1 queries

### 5.2 时间效率
- **小规模**（< 100 records）: < 100ms
- **中规模**（100-1000 records）: < 500ms
- **大规模**（> 1000 records）: < 2s

### 5.3 内存使用
- **每条记录**: < 1 KB overhead
- **大结果集**（10K records）: < 20 MB
- **嵌套关系**: 内存增长线性

---

## 6. 测试数据规模

### 6.1 Small Scale
- Organizations: 2
- Teams: 4
- Users: 12
- Projects: 8
- Tasks: 40

### 6.2 Medium Scale
- Organizations: 5
- Teams: 20
- Users: 160
- Projects: 100
- Tasks: 1500

### 6.3 Large Scale
- Organizations: 10
- Teams: 100
- Users: 2000
- Projects: 1000
- Tasks: 30000

---

## 7. 实施注意事项

### 7.1 测试隔离
- 每个测试使用独立数据集
- 清理缓存影响
- 控制并发干扰

### 7.2 测量精度
- 多次运行取平均
- 排除异常值
- 预热运行

### 7.3 内存分析
- 使用 tracemalloc 精确测量
- 区分 Python 对象和数据库数据
- 考虑缓存影响

---

本实施方案提供了预加载性能基准测试的完整框架。