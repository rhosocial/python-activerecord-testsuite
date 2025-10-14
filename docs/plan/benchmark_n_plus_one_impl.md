# 关系加载基准：N+1问题测试实施方案

## 1. 测试目标

本测试套件专门针对 ActiveRecord 中的 N+1 查询问题进行基准测试。N+1 问题是 ORM 中最常见的性能瓶颈之一，发生在加载关系时。测试将对比懒加载和预加载的性能差异。

**核心验证点：**
- 懒加载导致的 N+1 查询问题
- 预加载（eager loading）优化效果
- 不同关系类型的 N+1 表现
- 嵌套关系的查询数爆炸
- 查询数和执行时间的对比

**业务价值：**
- 识别和量化 N+1 问题的影响
- 验证预加载机制的有效性
- 为开发者提供优化指导
- 建立性能基准

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict, Any
from rhosocial.activerecord import ActiveRecord

class IN1BenchmarkProvider(ABC):
    """N+1 问题基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_n1_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # Author
        Type[ActiveRecord],  # Post
        Type[ActiveRecord],  # Comment
        Type[ActiveRecord],  # Tag
        Type[ActiveRecord]   # Category
    ]:
        """
        设置 N+1 测试模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 5 个模型类的元组：
            - Author: 作者（has_many posts）
            - Post: 文章（belongs_to author, has_many comments, has_many tags）
            - Comment: 评论（belongs_to post）
            - Tag: 标签（belongs_to post）
            - Category: 分类（has_many posts）
        """
        pass
    
    @abstractmethod
    def populate_n1_test_data(
        self,
        authors: int = 10,
        posts_per_author: int = 5,
        comments_per_post: int = 3,
        tags_per_post: int = 2
    ) -> Dict[str, Any]:
        """
        填充测试数据。
        
        Args:
            authors: 作者数量
            posts_per_author: 每个作者的文章数
            comments_per_post: 每篇文章的评论数
            tags_per_post: 每篇文章的标签数
            
        Returns:
            包含统计信息的字典
        """
        pass
    
    @abstractmethod
    def get_query_counter(self) -> 'QueryCounter':
        """
        获取查询计数器实例。
        
        Returns:
            查询计数器对象，用于统计执行的查询数量
        """
        pass
    
    @abstractmethod
    def cleanup_n1_data(self, scenario: str):
        """清理 N+1 测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Tuple, Type, Dict, Any
from rhosocial.activerecord import ActiveRecord
import time

class QueryCounter:
    """查询计数器，用于统计SQL查询数量。"""
    
    def __init__(self):
        self.query_count = 0
        self.queries = []
        self._enabled = False
    
    def start(self):
        """开始计数。"""
        self.query_count = 0
        self.queries.clear()
        self._enabled = True
    
    def stop(self):
        """停止计数。"""
        self._enabled = False
    
    def record_query(self, sql: str, params: Any = None):
        """记录一次查询。"""
        if self._enabled:
            self.query_count += 1
            self.queries.append({
                'sql': sql,
                'params': params,
                'timestamp': time.time()
            })
    
    def get_count(self) -> int:
        """获取查询数量。"""
        return self.query_count
    
    def get_queries(self) -> list:
        """获取所有查询记录。"""
        return self.queries.copy()
    
    def reset(self):
        """重置计数器。"""
        self.query_count = 0
        self.queries.clear()


@pytest.fixture
def n1_models(request) -> Tuple[
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord]
]:
    """
    提供 N+1 测试模型。
    
    Returns:
        (Author, Post, Comment, Tag, Category)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("n1_benchmark_provider")
    
    models = provider.setup_n1_models(scenario)
    
    yield models
    
    provider.cleanup_n1_data(scenario)


@pytest.fixture
def n1_test_data(n1_models, request):
    """
    填充测试数据。
    
    根据测试规模参数填充不同数量的数据。
    """
    provider = request.getfixturevalue("n1_benchmark_provider")
    
    # 根据 pytest marker 确定数据规模
    markers = [m.name for m in request.node.iter_markers()]
    
    if 'small_scale' in markers:
        stats = provider.populate_n1_test_data(
            authors=5,
            posts_per_author=3,
            comments_per_post=2,
            tags_per_post=2
        )
    elif 'medium_scale' in markers:
        stats = provider.populate_n1_test_data(
            authors=20,
            posts_per_author=10,
            comments_per_post=5,
            tags_per_post=3
        )
    elif 'large_scale' in markers:
        stats = provider.populate_n1_test_data(
            authors=100,
            posts_per_author=20,
            comments_per_post=10,
            tags_per_post=5
        )
    else:
        # 默认：小规模
        stats = provider.populate_n1_test_data(
            authors=10,
            posts_per_author=5,
            comments_per_post=3,
            tags_per_post=2
        )
    
    yield stats


@pytest.fixture
def query_counter(request):
    """提供查询计数器。"""
    provider = request.getfixturevalue("n1_benchmark_provider")
    counter = provider.get_query_counter()
    
    yield counter
    
    counter.stop()
    counter.reset()


@pytest.fixture
def benchmark_metrics():
    """提供基准测试指标收集器。"""
    class BenchmarkMetrics:
        def __init__(self):
            self.lazy_queries = 0
            self.lazy_time = 0.0
            self.eager_queries = 0
            self.eager_time = 0.0
        
        def calculate_improvement(self):
            """计算改进百分比。"""
            query_reduction = ((self.lazy_queries - self.eager_queries) / 
                              self.lazy_queries * 100 if self.lazy_queries > 0 else 0)
            time_reduction = ((self.lazy_time - self.eager_time) / 
                             self.lazy_time * 100 if self.lazy_time > 0 else 0)
            return {
                'query_reduction_percent': query_reduction,
                'time_reduction_percent': time_reduction,
                'queries_saved': self.lazy_queries - self.eager_queries
            }
    
    return BenchmarkMetrics()
```

---

## 4. 测试类和函数签名

### 4.1 Belongs-To 关系的 N+1

```python
import pytest
import time

@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestBelongsToN1:
    """测试 belongs_to 关系的 N+1 问题。"""
    
    def test_lazy_loading_baseline(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试懒加载基准（产生 N+1 问题）。
        
        验证点：
        1. 加载所有 Post，然后访问每个 Post 的 Author
        2. 应该产生 1 + N 次查询（1次查询posts，N次查询authors）
        3. 记录查询数和执行时间
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        # 开始计数
        query_counter.start()
        start_time = time.time()
        
        # 懒加载：产生 N+1
        posts = Post.all()  # 1 query
        authors = []
        for post in posts:
            authors.append(post.author.username)  # N queries
        
        end_time = time.time()
        query_counter.stop()
        
        # 记录指标
        benchmark_metrics.lazy_queries = query_counter.get_count()
        benchmark_metrics.lazy_time = end_time - start_time
        
        # 验证产生了 N+1 查询
        expected_queries = 1 + len(posts)  # 1 + N
        assert query_counter.get_count() >= expected_queries
    
    def test_eager_loading_optimization(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试预加载优化。
        
        验证点：
        1. 使用 with_('author') 预加载
        2. 应该只产生 2 次查询（1次posts，1次authors）
        3. 对比懒加载的改进
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        # 开始计数
        query_counter.start()
        start_time = time.time()
        
        # 预加载：解决 N+1
        posts = Post.with_('author').all()  # 2 queries
        authors = []
        for post in posts:
            authors.append(post.author.username)  # No additional queries
        
        end_time = time.time()
        query_counter.stop()
        
        # 记录指标
        benchmark_metrics.eager_queries = query_counter.get_count()
        benchmark_metrics.eager_time = end_time - start_time
        
        # 验证只有 2 次查询
        assert query_counter.get_count() == 2
        
        # 计算改进
        improvement = benchmark_metrics.calculate_improvement()
        assert improvement['query_reduction_percent'] > 50  # 至少减少 50% 查询


### 4.2 Has-Many 关系的 N+1

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestHasManyN1:
    """测试 has_many 关系的 N+1 问题。"""
    
    def test_lazy_loading_comments(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试懒加载评论（has_many）。
        
        验证点：
        1. 加载 Posts，然后访问每个 Post 的 Comments
        2. 产生 1 + N 次查询
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        query_counter.start()
        start_time = time.time()
        
        posts = Post.all()  # 1 query
        comment_counts = []
        for post in posts:
            comment_counts.append(len(post.comments))  # N queries
        
        end_time = time.time()
        query_counter.stop()
        
        benchmark_metrics.lazy_queries = query_counter.get_count()
        benchmark_metrics.lazy_time = end_time - start_time
        
        # 验证 N+1
        expected_queries = 1 + len(posts)
        assert query_counter.get_count() >= expected_queries
    
    def test_eager_loading_comments(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试预加载评论。
        
        验证点：
        1. 使用 with_('comments') 预加载
        2. 只产生 2 次查询
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        query_counter.start()
        start_time = time.time()
        
        posts = Post.with_('comments').all()  # 2 queries
        comment_counts = []
        for post in posts:
            comment_counts.append(len(post.comments))  # No additional queries
        
        end_time = time.time()
        query_counter.stop()
        
        benchmark_metrics.eager_queries = query_counter.get_count()
        benchmark_metrics.eager_time = end_time - start_time
        
        assert query_counter.get_count() == 2
        
        improvement = benchmark_metrics.calculate_improvement()
        assert improvement['query_reduction_percent'] > 50


### 4.3 嵌套关系的 N+1

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestNestedRelationN1:
    """测试嵌套关系的 N+1 问题。"""
    
    def test_nested_lazy_loading(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试嵌套关系懒加载。
        
        验证点：
        1. Authors -> Posts -> Comments 三层关系
        2. 查询数爆炸：1 + N1 + N1*N2
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        query_counter.start()
        start_time = time.time()
        
        authors = Author.all()  # 1 query
        total_comments = 0
        for author in authors:
            for post in author.posts:  # N1 queries
                total_comments += len(post.comments)  # N1 * N2 queries
        
        end_time = time.time()
        query_counter.stop()
        
        benchmark_metrics.lazy_queries = query_counter.get_count()
        benchmark_metrics.lazy_time = end_time - start_time
        
        # 验证嵌套 N+1
        # 1 (authors) + N1 (posts per author) + N1*N2 (comments per post)
        assert query_counter.get_count() > len(authors) * 2
    
    def test_nested_eager_loading(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试嵌套关系预加载。
        
        验证点：
        1. 使用 with_('posts.comments') 预加载
        2. 只产生 3 次查询
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        query_counter.start()
        start_time = time.time()
        
        authors = Author.with_('posts.comments').all()  # 3 queries
        total_comments = 0
        for author in authors:
            for post in author.posts:
                total_comments += len(post.comments)  # No additional queries
        
        end_time = time.time()
        query_counter.stop()
        
        benchmark_metrics.eager_queries = query_counter.get_count()
        benchmark_metrics.eager_time = end_time - start_time
        
        assert query_counter.get_count() == 3
        
        improvement = benchmark_metrics.calculate_improvement()
        assert improvement['query_reduction_percent'] > 80  # 巨大改进


### 4.4 多关系同时加载

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.medium_scale
class TestMultipleRelationN1:
    """测试同时加载多个关系的 N+1 问题。"""
    
    def test_multiple_lazy_loading(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试多关系懒加载。
        
        验证点：
        1. Post -> Author, Comments, Tags
        2. 查询数：1 + N*3 (author + comments + tags for each post)
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        query_counter.start()
        start_time = time.time()
        
        posts = Post.all()  # 1 query
        for post in posts:
            author_name = post.author.username  # N queries
            comment_count = len(post.comments)  # N queries
            tag_names = [tag.name for tag in post.tags]  # N queries
        
        end_time = time.time()
        query_counter.stop()
        
        benchmark_metrics.lazy_queries = query_counter.get_count()
        benchmark_metrics.lazy_time = end_time - start_time
        
        # 验证：1 + N*3
        expected_queries = 1 + len(posts) * 3
        assert query_counter.get_count() >= expected_queries
    
    def test_multiple_eager_loading(
        self,
        n1_models,
        n1_test_data,
        query_counter,
        benchmark_metrics
    ):
        """
        测试多关系预加载。
        
        验证点：
        1. with_('author', 'comments', 'tags')
        2. 只产生 4 次查询
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        query_counter.start()
        start_time = time.time()
        
        posts = Post.with_('author', 'comments', 'tags').all()  # 4 queries
        for post in posts:
            author_name = post.author.username
            comment_count = len(post.comments)
            tag_names = [tag.name for tag in post.tags]
        
        end_time = time.time()
        query_counter.stop()
        
        benchmark_metrics.eager_queries = query_counter.get_count()
        benchmark_metrics.eager_time = end_time - start_time
        
        assert query_counter.get_count() == 4
        
        improvement = benchmark_metrics.calculate_improvement()
        assert improvement['query_reduction_percent'] > 70


### 4.5 不同数据规模的性能对比

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.parametrize("scale,authors,posts_per_author", [
    ("small", 5, 3),
    ("medium", 20, 10),
    ("large", 100, 20)
])
class TestScalableN1:
    """测试不同数据规模下的 N+1 影响。"""
    
    def test_n1_impact_by_scale(
        self,
        n1_models,
        query_counter,
        benchmark_metrics,
        scale,
        authors,
        posts_per_author
    ):
        """
        测试数据规模对 N+1 的影响。
        
        验证点：
        1. 数据量增加，N+1 问题的影响成倍增长
        2. 预加载的改进效果在大数据量时更明显
        """
        Author, Post, Comment, Tag, Category = n1_models
        
        # 填充指定规模的数据
        provider = pytest.config.getoption("n1_benchmark_provider")
        provider.populate_n1_test_data(
            authors=authors,
            posts_per_author=posts_per_author,
            comments_per_post=3,
            tags_per_post=2
        )
        
        # 测试懒加载
        query_counter.start()
        lazy_start = time.time()
        posts = Post.all()
        for post in posts:
            _ = post.author.username
        lazy_end = time.time()
        lazy_queries = query_counter.get_count()
        query_counter.reset()
        
        # 测试预加载
        query_counter.start()
        eager_start = time.time()
        posts = Post.with_('author').all()
        for post in posts:
            _ = post.author.username
        eager_end = time.time()
        eager_queries = query_counter.get_count()
        
        # 记录和分析
        lazy_time = lazy_end - lazy_start
        eager_time = eager_end - eager_start
        
        print(f"\nScale: {scale}")
        print(f"Lazy: {lazy_queries} queries, {lazy_time:.4f}s")
        print(f"Eager: {eager_queries} queries, {eager_time:.4f}s")
        print(f"Improvement: {(lazy_queries - eager_queries) / lazy_queries * 100:.1f}% queries saved")
        
        # 验证改进随规模增加
        assert eager_queries <= 2
        assert lazy_queries > eager_queries * 2
```

---

## 5. 性能基准目标

### 5.1 查询数减少
- **目标**: 预加载应减少 80%+ 查询数
- **小规模**（10 posts）: 从 11 降到 2 查询
- **中规模**（100 posts）: 从 101 降到 2 查询
- **大规模**（1000 posts）: 从 1001 降到 2 查询

### 5.2 执行时间改进
- **目标**: 预加载应减少 60%+ 执行时间
- **因素**: 网络延迟、数据库开销
- **小规模**: 可能改进不明显（数据量小）
- **大规模**: 改进显著（减少往返次数）

### 5.3 嵌套关系优化
- **2层嵌套**: 从 1+N1+N1*N2 降到 3 查询
- **3层嵌套**: 从指数级查询降到固定查询数
- **改进率**: > 90% 查询数减少

---

## 6. 测试数据规模

### 6.1 Small Scale
- Authors: 5
- Posts: 15 (3 per author)
- Comments: 30 (2 per post)
- Tags: 30 (2 per post)

### 6.2 Medium Scale
- Authors: 20
- Posts: 200 (10 per author)
- Comments: 1000 (5 per post)
- Tags: 600 (3 per post)

### 6.3 Large Scale
- Authors: 100
- Posts: 2000 (20 per author)
- Comments: 20000 (10 per post)
- Tags: 10000 (5 per post)

---

## 7. 所需能力

```python
from rhosocial.activerecord.testsuite.utils import requires_capabilities
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    JoinCapability
)

# N+1 测试主要依赖 JOIN 能力
@requires_capabilities(
    (CapabilityCategory.JOIN, JoinCapability.LEFT_JOIN)
)
def test_eager_loading_with_join(n1_models, n1_test_data):
    """预加载通常使用 LEFT JOIN 实现。"""
    pass
```

---

## 8. 实施注意事项

### 8.1 查询计数
- 精确统计所有 SQL 查询
- 区分 SELECT、INSERT、UPDATE
- 记录查询时间戳

### 8.2 公平对比
- 相同的数据集
- 相同的操作顺序
- 隔离外部因素（缓存、网络）

### 8.3 结果展示
- 查询数对比图表
- 时间对比图表
- 改进百分比
- 数据规模影响曲线

---

本实施方案提供了 N+1 问题基准测试的完整框架。