# 内存规模基准：缓存性能测试实施方案

## 1. 测试目标

本测试套件评估 ActiveRecord 缓存机制的性能和效率。缓存是提升应用性能的重要手段，能够显著减少数据库查询次数和响应时间。

**核心验证点：**
- 查询结果缓存的命中率
- 身份映射（Identity Map）的效果
- 缓存对性能的提升
- 缓存失效策略的影响
- 内存开销与性能收益的权衡
- 缓存一致性维护

**业务价值：**
- 优化缓存策略
- 提高应用响应速度
- 减少数据库负载
- 改善用户体验

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, Dict, Any, Optional
from rhosocial.activerecord import ActiveRecord

class ICacheBenchmarkProvider(ABC):
    """缓存性能基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_cache_test_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # CachedModel
        Type[ActiveRecord]   # RelatedModel
    ]:
        """
        设置缓存测试模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 2 个模型类的元组
        """
        pass
    
    @abstractmethod
    def populate_cache_test_data(
        self,
        record_count: int,
        model_class: Type[ActiveRecord]
    ) -> Dict[str, Any]:
        """
        填充缓存测试数据。
        
        Args:
            record_count: 记录数量
            model_class: 模型类
            
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    def enable_query_cache(self):
        """启用查询结果缓存。"""
        pass
    
    @abstractmethod
    def disable_query_cache(self):
        """禁用查询结果缓存。"""
        pass
    
    @abstractmethod
    def clear_cache(self):
        """清除所有缓存。"""
        pass
    
    @abstractmethod
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息。
        
        Returns:
            包含命中次数、未命中次数、命中率等统计
        """
        pass
    
    @abstractmethod
    def enable_identity_map(self):
        """启用身份映射。"""
        pass
    
    @abstractmethod
    def disable_identity_map(self):
        """禁用身份映射。"""
        pass
    
    @abstractmethod
    def get_memory_profiler(self) -> 'MemoryProfiler':
        """获取内存分析器。"""
        pass
    
    @abstractmethod
    def cleanup_cache_test(self, scenario: str):
        """清理缓存测试数据。"""
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

class CacheMetrics:
    """缓存性能指标收集器。"""
    
    def __init__(self):
        self.queries_with_cache = 0
        self.queries_without_cache = 0
        self.time_with_cache = 0.0
        self.time_without_cache = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
    
    @property
    def hit_rate(self) -> float:
        """计算缓存命中率。"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0
    
    @property
    def speedup(self) -> float:
        """计算加速比。"""
        if self.time_with_cache > 0:
            return self.time_without_cache / self.time_with_cache
        return 0
    
    def print_report(self):
        """打印性能报告。"""
        print(f"\nCache Performance Report:")
        print(f"  Hit rate: {self.hit_rate:.1f}%")
        print(f"  Hits: {self.cache_hits}")
        print(f"  Misses: {self.cache_misses}")
        
        if self.time_without_cache > 0 and self.time_with_cache > 0:
            print(f"  Without cache: {self.time_without_cache:.4f}s")
            print(f"  With cache: {self.time_with_cache:.4f}s")
            print(f"  Speedup: {self.speedup:.2f}x")


@pytest.fixture
def cache_test_models(request) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
    """
    提供缓存测试模型。
    
    Returns:
        (CachedModel, RelatedModel)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("cache_benchmark_provider")
    
    models = provider.setup_cache_test_models(scenario)
    
    yield models
    
    provider.cleanup_cache_test(scenario)


@pytest.fixture
def cache_metrics():
    """提供缓存指标收集器。"""
    return CacheMetrics()


@pytest.fixture
def memory_profiler(request):
    """提供内存分析器。"""
    provider = request.getfixturevalue("cache_benchmark_provider")
    return provider.get_memory_profiler()


@pytest.fixture
def cache_enabled(request):
    """启用缓存的上下文。"""
    provider = request.getfixturevalue("cache_benchmark_provider")
    
    class CacheContext:
        def __enter__(self):
            provider.enable_query_cache()
            provider.enable_identity_map()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            provider.disable_query_cache()
            provider.disable_identity_map()
            provider.clear_cache()
    
    return CacheContext()
```

---

## 4. 测试类和函数签名

### 4.1 查询结果缓存

```python
import pytest
import time

@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestQueryCache:
    """测试查询结果缓存。"""
    
    def test_cache_hit_rate(
        self,
        cache_test_models,
        cache_metrics
    ):
        """
        测试缓存命中率。
        
        验证点：
        1. 重复查询的命中率
        2. 不同查询的命中率
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        # 填充数据
        provider.populate_cache_test_data(100, CachedModel)
        
        # 启用缓存
        provider.enable_query_cache()
        provider.clear_cache()
        
        # 执行重复查询
        queries = [
            lambda: CachedModel.where(value__gte=10).all(),
            lambda: CachedModel.where(value__lt=50).all(),
            lambda: CachedModel.limit(10).all()
        ]
        
        # 每个查询执行3次
        for query_func in queries:
            for _ in range(3):
                result = query_func()
                _ = len(result)
        
        # 获取缓存统计
        cache_stats = provider.get_cache_statistics()
        
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
        
        print(f"\nQuery Cache Hit Rate:")
        print(f"  Hits: {hits}")
        print(f"  Misses: {misses}")
        print(f"  Hit rate: {hit_rate:.1f}%")
        
        # 预期：每个查询首次未命中，后续2次命中
        # 3个查询 * (1未命中 + 2命中) = 3未命中 + 6命中
        # 命中率应该约为 66.7%
        assert hit_rate > 50, f"Cache hit rate too low: {hit_rate:.1f}%"
    
    def test_cache_performance_improvement(
        self,
        cache_test_models,
        cache_metrics
    ):
        """
        测试缓存对性能的提升。
        
        验证点：
        1. 有缓存 vs 无缓存的查询时间
        2. 加速比
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(1000, CachedModel)
        
        iterations = 50
        
        # 无缓存基准
        provider.disable_query_cache()
        
        start_time = time.time()
        for _ in range(iterations):
            records = CachedModel.where(value__gte=100).all()
            _ = len(records)
        cache_metrics.time_without_cache = time.time() - start_time
        cache_metrics.queries_without_cache = iterations
        
        # 有缓存
        provider.enable_query_cache()
        provider.clear_cache()
        
        start_time = time.time()
        for _ in range(iterations):
            records = CachedModel.where(value__gte=100).all()
            _ = len(records)
        cache_metrics.time_with_cache = time.time() - start_time
        cache_metrics.queries_with_cache = iterations
        
        # 获取缓存统计
        cache_stats = provider.get_cache_statistics()
        cache_metrics.cache_hits = cache_stats.get('hits', 0)
        cache_metrics.cache_misses = cache_stats.get('misses', 0)
        
        cache_metrics.print_report()
        
        # 期望至少有 2x 加速
        assert cache_metrics.speedup > 2, f"Cache speedup too low: {cache_metrics.speedup:.2f}x"
    
    def test_cache_invalidation(
        self,
        cache_test_models
    ):
        """
        测试缓存失效。
        
        验证点：
        1. 数据更新后缓存自动失效
        2. 失效策略的正确性
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(100, CachedModel)
        provider.enable_query_cache()
        provider.clear_cache()
        
        # 首次查询（未命中）
        results1 = CachedModel.where(value__gte=50).all()
        count1 = len(results1)
        
        # 再次查询（命中）
        results2 = CachedModel.where(value__gte=50).all()
        count2 = len(results2)
        
        assert count1 == count2
        
        # 更新数据
        record = CachedModel.first()
        record.value = 100
        record.save()
        
        # 查询应该获取新数据（缓存已失效）
        results3 = CachedModel.where(value__gte=50).all()
        count3 = len(results3)
        
        # 可能比之前多一条（取决于失效策略）
        print(f"\nCache Invalidation:")
        print(f"  Before update: {count1} records")
        print(f"  After update: {count3} records")


### 4.2 身份映射

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestIdentityMap:
    """测试身份映射（Identity Map）。"""
    
    def test_identity_map_effectiveness(
        self,
        cache_test_models
    ):
        """
        测试身份映射的有效性。
        
        验证点：
        1. 同一ID的对象返回同一实例
        2. 减少对象创建开销
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(100, CachedModel)
        provider.enable_identity_map()
        
        # 多次查询同一ID
        record_id = 1
        
        obj1 = CachedModel.find(record_id)
        obj2 = CachedModel.find(record_id)
        obj3 = CachedModel.find(record_id)
        
        # 应该是同一对象实例
        assert obj1 is obj2, "Identity map failed: different instances"
        assert obj2 is obj3, "Identity map failed: different instances"
        
        print(f"\nIdentity Map Test:")
        print(f"  obj1 is obj2: {obj1 is obj2}")
        print(f"  obj2 is obj3: {obj2 is obj3}")
        print(f"  All are same instance: True")
    
    def test_identity_map_memory_overhead(
        self,
        cache_test_models,
        memory_profiler
    ):
        """
        测试身份映射的内存开销。
        
        验证点：
        1. 身份映射占用的额外内存
        2. 内存增长模式
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(1000, CachedModel)
        
        # 无身份映射
        provider.disable_identity_map()
        
        memory_profiler.start()
        records_without_map = []
        for i in range(1, 101):
            rec = CachedModel.find(i)
            records_without_map.append(rec)
        memory_profiler.stop()
        
        usage_without = memory_profiler.get_usage()
        
        # 有身份映射
        provider.enable_identity_map()
        
        memory_profiler.start()
        records_with_map = []
        for i in range(1, 101):
            rec = CachedModel.find(i)
            records_with_map.append(rec)
        memory_profiler.stop()
        
        usage_with = memory_profiler.get_usage()
        
        overhead = usage_with['used'] - usage_without['used']
        overhead_percent = (overhead / usage_without['used'] * 100) if usage_without['used'] > 0 else 0
        
        print(f"\nIdentity Map Memory Overhead:")
        print(f"  Without: {usage_without['used'] / 1024:.2f} KB")
        print(f"  With: {usage_with['used'] / 1024:.2f} KB")
        print(f"  Overhead: {overhead / 1024:.2f} KB ({overhead_percent:.1f}%)")
    
    def test_identity_map_consistency(
        self,
        cache_test_models
    ):
        """
        测试身份映射的一致性。
        
        验证点：
        1. 修改对象后，其他引用看到变化
        2. 数据一致性
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(100, CachedModel)
        provider.enable_identity_map()
        
        # 获取同一对象的两个引用
        obj1 = CachedModel.find(1)
        obj2 = CachedModel.find(1)
        
        original_value = obj1.value
        
        # 修改 obj1
        obj1.value = original_value + 100
        
        # obj2 应该看到变化（因为是同一实例）
        assert obj2.value == original_value + 100, "Identity map consistency failed"
        
        print(f"\nIdentity Map Consistency:")
        print(f"  Original value: {original_value}")
        print(f"  After modification via obj1: {obj2.value}")
        print(f"  Consistency maintained: True")


### 4.3 缓存内存开销

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.medium_scale
class TestCacheMemoryOverhead:
    """测试缓存的内存开销。"""
    
    def test_cache_size_growth(
        self,
        cache_test_models,
        memory_profiler
    ):
        """
        测试缓存大小随查询增长。
        
        验证点：
        1. 缓存内存占用
        2. 与缓存项数量的关系
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(10000, CachedModel)
        provider.enable_query_cache()
        provider.clear_cache()
        
        memory_profiler.start()
        
        # 执行不同的查询（每个都会被缓存）
        for i in range(0, 100, 10):
            records = CachedModel.where(value__gte=i).all()
            _ = len(records)
            
            memory_profiler.snapshot(f"query_{i // 10}")
        
        memory_profiler.stop()
        
        usage = memory_profiler.get_usage()
        
        print(f"\nCache Memory Growth:")
        print(f"  Initial: {usage['start'] / 1024 / 1024:.2f} MB")
        print(f"  Final: {usage['current'] / 1024 / 1024:.2f} MB")
        print(f"  Growth: {usage['used'] / 1024 / 1024:.2f} MB")
        
        # 打印快照
        if usage['snapshots']:
            print(f"  Snapshots:")
            for snap in usage['snapshots'][::2]:  # 每隔一个打印
                print(f"    {snap['label']}: {snap['current'] / 1024 / 1024:.2f} MB")
    
    def test_cache_vs_no_cache_memory(
        self,
        cache_test_models,
        memory_profiler
    ):
        """
        对比有缓存和无缓存的内存使用。
        
        验证点：
        1. 缓存的额外内存开销
        2. 内存与性能的权衡
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(5000, CachedModel)
        
        queries = 50
        
        # 无缓存
        provider.disable_query_cache()
        
        memory_profiler.start()
        start_time = time.time()
        
        for i in range(queries):
            records = CachedModel.where(value__gte=i * 10).all()
            _ = len(records)
        
        time_without = time.time() - start_time
        memory_profiler.stop()
        usage_without = memory_profiler.get_usage()
        
        # 有缓存
        provider.enable_query_cache()
        provider.clear_cache()
        
        memory_profiler.start()
        start_time = time.time()
        
        for i in range(queries):
            records = CachedModel.where(value__gte=i * 10).all()
            _ = len(records)
        
        time_with = time.time() - start_time
        memory_profiler.stop()
        usage_with = memory_profiler.get_usage()
        
        memory_overhead = usage_with['peak'] - usage_without['peak']
        time_saving = (time_without - time_with) / time_without * 100
        
        print(f"\nCache Memory vs Performance Trade-off:")
        print(f"  Without cache:")
        print(f"    Time: {time_without:.4f}s")
        print(f"    Memory: {usage_without['peak'] / 1024 / 1024:.2f} MB")
        print(f"  With cache:")
        print(f"    Time: {time_with:.4f}s")
        print(f"    Memory: {usage_with['peak'] / 1024 / 1024:.2f} MB")
        print(f"  Trade-off:")
        print(f"    Time saved: {time_saving:.1f}%")
        print(f"    Memory overhead: {memory_overhead / 1024 / 1024:.2f} MB")


### 4.4 缓存失效策略

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestCacheInvalidation:
    """测试缓存失效策略。"""
    
    def test_time_based_invalidation(
        self,
        cache_test_models
    ):
        """
        测试基于时间的缓存失效（如果支持）。
        
        验证点：
        1. TTL 过期后缓存失效
        2. 失效时间的准确性
        """
        # 如果后端支持 TTL
        pytest.skip("TTL-based invalidation not implemented yet")
    
    def test_size_based_eviction(
        self,
        cache_test_models
    ):
        """
        测试基于大小的缓存驱逐（如果支持）。
        
        验证点：
        1. 缓存达到最大大小时驱逐旧项
        2. LRU 或其他驱逐策略
        """
        # 如果后端支持大小限制
        pytest.skip("Size-based eviction not implemented yet")
    
    def test_manual_invalidation(
        self,
        cache_test_models
    ):
        """
        测试手动失效。
        
        验证点：
        1. clear_cache() 清除所有缓存
        2. 选择性失效
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(100, CachedModel)
        provider.enable_query_cache()
        provider.clear_cache()
        
        # 执行查询（填充缓存）
        records1 = CachedModel.where(value__gte=50).all()
        _ = len(records1)
        
        cache_stats_before = provider.get_cache_statistics()
        hits_before = cache_stats_before.get('hits', 0)
        
        # 手动清除缓存
        provider.clear_cache()
        
        # 再次查询（应该未命中）
        records2 = CachedModel.where(value__gte=50).all()
        _ = len(records2)
        
        cache_stats_after = provider.get_cache_statistics()
        hits_after = cache_stats_after.get('hits', 0)
        misses_after = cache_stats_after.get('misses', 0)
        
        print(f"\nManual Invalidation:")
        print(f"  Hits before clear: {hits_before}")
        print(f"  Hits after clear: {hits_after}")
        print(f"  Misses after clear: {misses_after}")
        
        # 清除后的查询应该是未命中
        assert misses_after > 0, "Cache not properly cleared"


### 4.5 关系加载缓存

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestRelationCache:
    """测试关系加载的缓存。"""
    
    def test_relation_caching(
        self,
        cache_test_models
    ):
        """
        测试关系数据的缓存。
        
        验证点：
        1. 加载关系后缓存
        2. 再次访问时从缓存获取
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        # 设置关系数据
        # ...
        
        provider.enable_query_cache()
        provider.enable_identity_map()
        
        # 首次加载关系
        start_time = time.time()
        parent = CachedModel.find(1)
        children = parent.related_models  # 假设有关系
        _ = len(children)
        first_load_time = time.time() - start_time
        
        # 再次访问（应该从缓存）
        start_time = time.time()
        children2 = parent.related_models
        _ = len(children2)
        second_load_time = time.time() - start_time
        
        speedup = first_load_time / second_load_time if second_load_time > 0 else 0
        
        print(f"\nRelation Caching:")
        print(f"  First load: {first_load_time * 1000:.2f}ms")
        print(f"  Second load: {second_load_time * 1000:.2f}ms")
        print(f"  Speedup: {speedup:.2f}x")


### 4.6 缓存一致性

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestCacheConsistency:
    """测试缓存一致性。"""
    
    def test_write_through_consistency(
        self,
        cache_test_models
    ):
        """
        测试写穿透的一致性。
        
        验证点：
        1. 写入数据后立即可见
        2. 缓存与数据库一致
        """
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(100, CachedModel)
        provider.enable_query_cache()
        provider.enable_identity_map()
        
        # 查询并缓存
        record = CachedModel.find(1)
        original_value = record.value
        
        # 修改并保存
        record.value = original_value + 100
        record.save()
        
        # 重新查询（应该获取新值）
        record2 = CachedModel.find(1)
        
        assert record2.value == original_value + 100, "Cache consistency failed after write"
        
        print(f"\nWrite-Through Consistency:")
        print(f"  Original value: {original_value}")
        print(f"  Modified value: {original_value + 100}")
        print(f"  Queried value: {record2.value}")
        print(f"  Consistency: {'OK' if record2.value == original_value + 100 else 'FAILED'}")
    
    def test_concurrent_cache_access(
        self,
        cache_test_models
    ):
        """
        测试并发访问缓存的一致性。
        
        验证点：
        1. 多线程同时读缓存
        2. 读写混合场景
        3. 无竞态条件
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        CachedModel, RelatedModel = cache_test_models
        provider = pytest.config.getoption("cache_benchmark_provider")
        
        provider.populate_cache_test_data(100, CachedModel)
        provider.enable_query_cache()
        provider.enable_identity_map()
        
        def reader_worker():
            """读线程。"""
            for _ in range(50):
                record = CachedModel.find(1)
                _ = record.value
        
        def writer_worker():
            """写线程。"""
            for i in range(10):
                record = CachedModel.find(1)
                record.value += 1
                record.save()
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=10) as executor:
            reader_futures = [executor.submit(reader_worker) for _ in range(8)]
            writer_futures = [executor.submit(writer_worker) for _ in range(2)]
            
            for future in as_completed(reader_futures + writer_futures):
                future.result()
        
        # 验证最终值
        final_record = CachedModel.find(1)
        
        print(f"\nConcurrent Cache Access:")
        print(f"  Final value: {final_record.value}")
        print(f"  No errors occurred")
```

---

## 5. 性能基准目标

### 5.1 缓存命中率
- **重复查询**: > 90% 命中率
- **相似查询**: > 70% 命中率

### 5.2 性能提升
- **查询加速**: 2-10x（取决于查询复杂度）
- **身份映射**: 对象查找加速 5-20x

### 5.3 内存开销
- **查询缓存**: 每个缓存项 < 5 KB overhead
- **身份映射**: 每个对象 < 1 KB overhead
- **总开销**: < 原始数据的 20%

---

## 6. 测试数据规模

### 6.1 Small Scale
- 记录数: 100-1000
- 查询数: 50-100
- 用途: 功能验证、命中率测试

### 6.2 Medium Scale
- 记录数: 10000
- 查询数: 500-1000
- 用途: 性能测试、内存分析

### 6.3 Large Scale
- 记录数: 100000+
- 查询数: 5000+
- 用途: 压力测试、扩展性验证

---

## 7. 所需能力

```python
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    CacheCapability
)

optional_capabilities = [
    (CapabilityCategory.CACHE, CacheCapability.QUERY_CACHE),
    (CapabilityCategory.CACHE, CacheCapability.IDENTITY_MAP),
    (CapabilityCategory.CACHE, CacheCapability.CACHE_STATISTICS)
]
```

---

## 8. 实施注意事项

### 8.1 缓存策略
- 根据访问模式选择缓存粒度
- 平衡内存和性能
- 设置合理的失效策略

### 8.2 一致性保证
- 写操作后立即失效相关缓存
- 考虑分布式场景的缓存同步
- 监控缓存不一致问题

### 8.3 内存管理
- 设置缓存大小上限
- 实现缓存驱逐策略（LRU、LFU等）
- 监控内存使用

### 8.4 最佳实践
- 缓存频繁访问的数据
- 避免缓存易变数据
- 使用适当的缓存键
- 定期清理过期缓存

---

本实施方案提供了缓存性能基准测试的完整框架。