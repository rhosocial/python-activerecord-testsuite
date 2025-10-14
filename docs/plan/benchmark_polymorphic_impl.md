# 关系加载基准：多态关系测试实施方案

## 1. 测试目标

本测试套件专门针对 ActiveRecord 中的多态关系（Polymorphic Associations）进行基准测试。多态关系允许一个模型通过单一关联属于多种不同类型的模型，是灵活数据建模的重要特性。

**核心验证点：**
- 多态关联的查询性能
- 多态集合的加载效率
- 混合类型查询的优化
- 类型解析的开销
- 预加载对多态关系的支持
- 大规模多态数据的处理

**业务价值：**
- 评估多态关系的性能影响
- 验证多态关系的正确性
- 为使用多态关系提供性能指导
- 识别多态关系的性能瓶颈

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict, Any
from rhosocial.activerecord import ActiveRecord

class IPolymorphicBenchmarkProvider(ABC):
    """多态关系基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_polymorphic_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Article
        Type[ActiveRecord],  # Photo
        Type[ActiveRecord],  # Video
        Type[ActiveRecord],  # Comment (polymorphic)
        Type[ActiveRecord],  # Like (polymorphic)
        Type[ActiveRecord],  # Tag (polymorphic)
        Type[ActiveRecord]   # Activity (polymorphic)
    ]:
        """
        设置多态关系测试模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 8 个模型类的元组：
            - User: 用户
            - Article: 文章（可评论、可点赞、可标签、可活动）
            - Photo: 照片（可评论、可点赞、可标签、可活动）
            - Video: 视频（可评论、可点赞、可标签、可活动）
            - Comment: 评论（多态：commentable_type, commentable_id）
            - Like: 点赞（多态：likeable_type, likeable_id）
            - Tag: 标签（多态：taggable_type, taggable_id）
            - Activity: 活动记录（多态：subject_type, subject_id）
        """
        pass
    
    @abstractmethod
    def populate_polymorphic_data(
        self,
        users: int = 20,
        articles: int = 50,
        photos: int = 100,
        videos: int = 30,
        comments_per_content: int = 5,
        likes_per_content: int = 10,
        tags_per_content: int = 3
    ) -> Dict[str, Any]:
        """
        填充多态关系测试数据。
        
        Args:
            users: 用户数量
            articles: 文章数量
            photos: 照片数量
            videos: 视频数量
            comments_per_content: 每个内容的评论数
            likes_per_content: 每个内容的点赞数
            tags_per_content: 每个内容的标签数
            
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
    def cleanup_polymorphic_data(self, scenario: str):
        """清理多态关系测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Tuple, Type, Dict, Any
import time
from rhosocial.activerecord import ActiveRecord

@pytest.fixture
def polymorphic_models(request) -> Tuple[
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord]
]:
    """
    提供多态关系测试模型。
    
    Returns:
        (User, Article, Photo, Video, Comment, Like, Tag, Activity)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("polymorphic_benchmark_provider")
    
    models = provider.setup_polymorphic_models(scenario)
    
    yield models
    
    provider.cleanup_polymorphic_data(scenario)


@pytest.fixture
def polymorphic_test_data(polymorphic_models, request):
    """填充多态关系测试数据。"""
    provider = request.getfixturevalue("polymorphic_benchmark_provider")
    
    markers = [m.name for m in request.node.iter_markers()]
    
    if 'small_scale' in markers:
        stats = provider.populate_polymorphic_data(
            users=10,
            articles=20,
            photos=30,
            videos=10,
            comments_per_content=3,
            likes_per_content=5,
            tags_per_content=2
        )
    elif 'medium_scale' in markers:
        stats = provider.populate_polymorphic_data(
            users=50,
            articles=100,
            photos=200,
            videos=50,
            comments_per_content=8,
            likes_per_content=15,
            tags_per_content=4
        )
    elif 'large_scale' in markers:
        stats = provider.populate_polymorphic_data(
            users=200,
            articles=500,
            photos=1000,
            videos=200,
            comments_per_content=20,
            likes_per_content=50,
            tags_per_content=8
        )
    else:
        stats = provider.populate_polymorphic_data()
    
    yield stats


@pytest.fixture
def query_counter(request):
    """提供查询计数器。"""
    provider = request.getfixturevalue("polymorphic_benchmark_provider")
    counter = provider.get_query_counter()
    
    yield counter
    
    counter.stop()
    counter.reset()


@pytest.fixture
def memory_profiler(request):
    """提供内存分析器。"""
    provider = request.getfixturevalue("polymorphic_benchmark_provider")
    profiler = provider.get_memory_profiler()
    
    yield profiler


@pytest.fixture
def type_distribution():
    """提供类型分布统计工具。"""
    class TypeDistribution:
        def __init__(self):
            self.type_counts = {}
        
        def record(self, type_name: str):
            self.type_counts[type_name] = self.type_counts.get(type_name, 0) + 1
        
        def get_stats(self):
            total = sum(self.type_counts.values())
            return {
                'total': total,
                'types': self.type_counts,
                'distribution': {
                    k: v / total * 100 for k, v in self.type_counts.items()
                }
            }
    
    return TypeDistribution()
```

---

## 4. 测试类和函数签名

### 4.1 多态关联基础性能

```python
import pytest
import time

@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestPolymorphicAssociationBasics:
    """测试多态关联的基础性能。"""
    
    def test_polymorphic_query_single_type(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试查询单一类型的多态关联。
        
        验证点：
        1. 查询所有 Article 的评论
        2. 查询效率
        3. 类型过滤的开销
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        # 查询所有文章的评论
        article_comments = Comment.where(commentable_type='Article').all()
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Single type query: {len(article_comments)} comments")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
        
        assert query_counter.get_count() >= 1
    
    def test_polymorphic_query_multiple_types(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter,
        type_distribution
    ):
        """
        测试查询多种类型的多态关联。
        
        验证点：
        1. 查询所有评论（不管被评论对象类型）
        2. 统计类型分布
        3. 查询效率
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        all_comments = Comment.all()
        
        # 统计类型分布
        for comment in all_comments:
            type_distribution.record(comment.commentable_type)
        
        end_time = time.time()
        query_counter.stop()
        
        stats = type_distribution.get_stats()
        print(f"Total comments: {stats['total']}")
        print(f"Type distribution: {stats['distribution']}")
        print(f"Time: {end_time - start_time:.4f}s")
    
    def test_polymorphic_belongs_to(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试多态 belongs_to 关系访问。
        
        验证点：
        1. 从 Comment 访问 commentable（Article/Photo/Video）
        2. 类型解析开销
        3. N+1 问题
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        comments = Comment.limit(10).all()
        
        for comment in comments:
            # 访问多态关系
            commentable = comment.commentable
            _ = commentable.id if commentable else None
        
        end_time = time.time()
        query_counter.stop()
        
        # 会产生 N+1 问题
        print(f"Polymorphic belongs_to: {query_counter.get_count()} queries")
        print(f"Time: {end_time - start_time:.4f}s")


### 4.2 多态集合性能

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.small_scale
class TestPolymorphicCollections:
    """测试多态集合的性能。"""
    
    def test_load_polymorphic_collection_lazy(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试懒加载多态集合。
        
        验证点：
        1. Article.comments（多态 has_many）
        2. 产生 N+1 问题
        3. 内存使用
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        articles = Article.all()
        
        total_comments = 0
        for article in articles:
            total_comments += len(article.comments)  # N queries
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        print(f"Lazy loading: {total_comments} comments")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
        print(f"Memory: {memory_profiler.get_usage()['used'] / 1024 / 1024:.2f} MB")
    
    def test_load_polymorphic_collection_eager(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试预加载多态集合。
        
        验证点：
        1. Article.with_('comments')
        2. 查询优化
        3. 与懒加载对比
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        articles = Article.with_('comments').all()
        
        total_comments = 0
        for article in articles:
            total_comments += len(article.comments)  # No additional queries
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        print(f"Eager loading: {total_comments} comments")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
        print(f"Memory: {memory_profiler.get_usage()['used'] / 1024 / 1024:.2f} MB")
    
    def test_mixed_type_collection(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试混合类型集合查询。
        
        验证点：
        1. 获取用户的所有活动（包含多种类型的对象）
        2. 类型解析性能
        3. 查询策略
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        # 获取用户的活动记录
        user = User.first()
        activities = Activity.where(user_id=user.id).all()
        
        # 访问不同类型的主体对象
        for activity in activities:
            subject = activity.subject  # 可能是 Article/Photo/Video
            _ = subject.id if subject else None
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Mixed type collection: {len(activities)} activities")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")


### 4.3 类型解析性能

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.medium_scale
class TestTypeResolution:
    """测试类型解析的性能开销。"""
    
    def test_type_resolution_overhead(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试类型解析的开销。
        
        验证点：
        1. 从 type 字符串到模型类的映射
        2. 解析时间
        3. 缓存效果
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        # 测试类型解析
        type_strings = ['Article', 'Photo', 'Video']
        
        start_time = time.time()
        
        # 模拟类型解析（具体实现取决于 ActiveRecord）
        for _ in range(1000):
            for type_str in type_strings:
                # 这里应该调用 ActiveRecord 的类型解析方法
                pass
        
        end_time = time.time()
        
        total_resolutions = 1000 * len(type_strings)
        avg_time = (end_time - start_time) / total_resolutions * 1000000  # 微秒
        
        print(f"Type resolution: {avg_time:.2f} μs per resolution")
    
    def test_polymorphic_query_with_type_filter(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试带类型过滤的多态查询。
        
        验证点：
        1. 查询特定类型的多态关联
        2. WHERE 子句的影响
        3. 索引使用情况
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        # 不同类型过滤的查询性能
        types_to_test = ['Article', 'Photo', 'Video']
        
        for content_type in types_to_test:
            query_counter.reset()
            query_counter.start()
            start_time = time.time()
            
            comments = Comment.where(commentable_type=content_type).all()
            
            end_time = time.time()
            query_counter.stop()
            
            print(f"{content_type}: {len(comments)} comments, "
                  f"{end_time - start_time:.4f}s, "
                  f"{query_counter.get_count()} queries")
    
    def test_polymorphic_join_performance(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试多态关系的 JOIN 性能。
        
        验证点：
        1. 多态关系的 JOIN 查询
        2. 与多次查询的对比
        3. 不同数据库的支持情况
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        # 测试 JOIN 查询（如果支持）
        # 注意：某些数据库可能不支持多态 JOIN
        pass


### 4.4 多态关系预加载优化

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.medium_scale
class TestPolymorphicEagerLoading:
    """测试多态关系的预加载优化。"""
    
    def test_eager_load_polymorphic_belongs_to(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试预加载多态 belongs_to。
        
        验证点：
        1. Comment.with_('commentable')
        2. 需要查询多个表（Article, Photo, Video）
        3. 查询数和性能
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        # 预加载多态关系
        comments = Comment.with_('commentable').all()
        
        # 访问多态对象
        for comment in comments:
            commentable = comment.commentable
            _ = commentable.id if commentable else None
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Eager load polymorphic: {len(comments)} comments")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
        
        # 查询数应该是：1 (comments) + N (每种类型一个查询)
        # 例如：1 + 3 = 4 (如果有 Article, Photo, Video)
    
    def test_eager_load_multiple_polymorphic_relations(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试预加载多个多态关系。
        
        验证点：
        1. Article.with_('comments', 'likes', 'tags')
        2. 多个多态集合的预加载
        3. 查询优化
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        articles = Article.with_('comments', 'likes', 'tags').all()
        
        for article in articles:
            _ = len(article.comments)
            _ = len(article.likes)
            _ = len(article.tags)
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Multiple polymorphic relations: {len(articles)} articles")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
    
    def test_nested_polymorphic_eager_loading(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试嵌套多态关系预加载。
        
        验证点：
        1. Article.with_('comments.user')
        2. 多态关系的嵌套加载
        3. 复杂查询的性能
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        articles = Article.with_('comments.user').all()
        
        for article in articles:
            for comment in article.comments:
                _ = comment.user.username
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Nested polymorphic: {len(articles)} articles")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")


### 4.5 大规模多态数据性能

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.large_scale
class TestLargeScalePolymorphic:
    """测试大规模多态数据的性能。"""
    
    def test_large_polymorphic_collection(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter,
        memory_profiler
    ):
        """
        测试大规模多态集合。
        
        验证点：
        1. 数千个多态记录
        2. 内存使用
        3. 查询性能
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        memory_profiler.start()
        start_time = time.time()
        
        # 查询所有评论（跨多种类型）
        all_comments = Comment.all()
        
        # 统计类型
        type_counts = {}
        for comment in all_comments:
            type_name = comment.commentable_type
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        end_time = time.time()
        memory_profiler.stop()
        query_counter.stop()
        
        memory_used_mb = memory_profiler.get_usage()['used'] / 1024 / 1024
        
        print(f"Total comments: {len(all_comments)}")
        print(f"Type distribution: {type_counts}")
        print(f"Time: {end_time - start_time:.4f}s")
        print(f"Memory: {memory_used_mb:.2f} MB")
        print(f"Memory per comment: {memory_used_mb * 1024 / len(all_comments):.2f} KB")
    
    def test_polymorphic_query_with_pagination(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试多态查询的分页性能。
        
        验证点：
        1. 分页查询多态数据
        2. OFFSET/LIMIT 性能
        3. 与全量查询对比
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        page_size = 20
        page_num = 1
        
        query_counter.start()
        start_time = time.time()
        
        # 分页查询
        comments = Comment.limit(page_size).offset((page_num - 1) * page_size).all()
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Paginated query: {len(comments)} comments")
        print(f"Time: {end_time - start_time:.4f}s")
    
    def test_polymorphic_aggregation(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试多态数据的聚合查询。
        
        验证点：
        1. GROUP BY commentable_type
        2. COUNT 每种类型的数量
        3. 聚合性能
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        # 按类型聚合
        type_stats = Comment.group('commentable_type').count()
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Aggregation results: {type_stats}")
        print(f"Time: {end_time - start_time:.4f}s")


### 4.6 多态关系的实际应用场景

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_relation
@pytest.mark.medium_scale
class TestPolymorphicRealWorldScenarios:
    """测试多态关系在实际应用中的性能。"""
    
    def test_activity_feed_with_polymorphic(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试活动流（多态对象的混合列表）。
        
        验证点：
        1. 时间线包含多种类型的活动
        2. 加载和显示性能
        3. 预加载优化
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        query_counter.start()
        start_time = time.time()
        
        # 获取用户的活动流
        user = User.first()
        activities = Activity.where(user_id=user.id).order_by('-created_at').limit(20).all()
        
        # 访问活动的主体对象
        for activity in activities:
            subject = activity.subject
            _ = subject.id if subject else None
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Activity feed: {len(activities)} items")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
    
    def test_search_across_polymorphic_types(
        self,
        polymorphic_models,
        polymorphic_test_data,
        query_counter
    ):
        """
        测试跨多态类型的搜索。
        
        验证点：
        1. 搜索所有可评论内容
        2. 按关键词过滤
        3. 查询效率
        """
        User, Article, Photo, Video, Comment, Like, Tag, Activity = polymorphic_models
        
        keyword = "test"
        
        query_counter.start()
        start_time = time.time()
        
        # 搜索多种类型的内容
        articles = Article.where(title__contains=keyword).all()
        photos = Photo.where(caption__contains=keyword).all()
        videos = Video.where(title__contains=keyword).all()
        
        total_results = len(articles) + len(photos) + len(videos)
        
        end_time = time.time()
        query_counter.stop()
        
        print(f"Cross-type search: {total_results} results")
        print(f"Queries: {query_counter.get_count()}")
        print(f"Time: {end_time - start_time:.4f}s")
```

---

## 5. 性能基准目标

### 5.1 类型解析开销
- **目标**: 类型解析时间 < 10 μs
- **缓存效果**: 首次解析后应缓存
- **批量解析**: 支持批量类型解析优化

### 5.2 查询效率
- **单类型查询**: 与普通查询相当
- **多类型查询**: 添加 WHERE 子句的小开销（< 10%）
- **预加载**: 每种类型增加 1 个查询

### 5.3 内存开销
- **类型标识**: 每条记录 < 100 bytes
- **大规模数据**: 内存增长线性
- **预加载**: 相比懒加载，内存增加 < 50%

---

## 6. 测试数据规模

### 6.1 Small Scale
- Users: 10
- Articles: 20
- Photos: 30
- Videos: 10
- Comments: 180
- Likes: 300
- Tags: 120

### 6.2 Medium Scale
- Users: 50
- Articles: 100
- Photos: 200
- Videos: 50
- Comments: 2800
- Likes: 5250
- Tags: 1400

### 6.3 Large Scale
- Users: 200
- Articles: 500
- Photos: 1000
- Videos: 200
- Comments: 34000
- Likes: 85000
- Tags: 13600

---

## 7. 所需能力

```python
from rhosocial.activerecord.testsuite.utils import requires_capabilities
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    IndexCapability,
    AggregateFunctionCapability
)

# 多态关系建议使用复合索引
@requires_capabilities(
    (CapabilityCategory.INDEX, IndexCapability.COMPOSITE_INDEX)
)
def test_polymorphic_with_composite_index(polymorphic_models):
    """多态关系使用 (type, id) 复合索引优化。"""
    pass
```

---

## 8. 实施注意事项

### 8.1 数据库设计
- 使用复合索引：(type, id)
- 类型字段应使用字符串或枚举
- 考虑分表策略（大规模数据）

### 8.2 查询优化
- 尽量使用类型过滤
- 预加载多态关系
- 批量查询不同类型

### 8.3 性能监控
- 监控类型解析时间
- 跟踪查询计划
- 分析索引使用情况

### 8.4 多态关系的权衡
- **优点**: 灵活的数据建模
- **缺点**: 查询复杂度增加
- **建议**: 适度使用，避免过度嵌套

---

本实施方案提供了多态关系基准测试的完整框架。