# 内存规模基准：大结果集测试实施方案

## 1. 测试目标

本测试套件评估 ActiveRecord 处理大结果集时的内存使用和性能表现。大结果集处理是许多应用场景的性能瓶颈，需要特别关注内存管理。

**核心验证点：**
- 不同大小结果集的内存占用
- 加载时间与结果集大小的关系
- 分页查询 vs 全量查询的对比
- 流式处理 vs 完全物化的对比
- 内存峰值和增长模式
- OOM（内存溢出）阈值

**业务价值：**
- 评估系统的数据处理能力
- 识别内存瓶颈
- 优化大数据查询策略
- 为容量规划提供数据

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, Iterator, List, Dict, Any
from rhosocial.activerecord import ActiveRecord

class ILargeResultSetBenchmarkProvider(ABC):
    """大结果集基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_large_dataset_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # LargeRecord
        Type[ActiveRecord]   # MediumRecord
    ]:
        """
        设置大数据集测试模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 2 个模型类的元组：
            - LargeRecord: 包含较多字段的记录
            - MediumRecord: 中等字段数的记录
        """
        pass
    
    @abstractmethod
    def populate_large_dataset(
        self,
        record_count: int,
        model_class: Type[ActiveRecord]
    ) -> Dict[str, Any]:
        """
        填充大量测试数据。
        
        Args:
            record_count: 记录数量
            model_class: 要填充的模型类
            
        Returns:
            包含统计信息的字典
        """
        pass
    
    @abstractmethod
    def get_memory_profiler(self) -> 'MemoryProfiler':
        """获取内存分析器。"""
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """检查后端是否支持流式查询。"""
        pass
    
    @abstractmethod
    def iterate_records(
        self,
        model_class: Type[ActiveRecord],
        batch_size: int = 1000
    ) -> Iterator[List[ActiveRecord]]:
        """
        流式迭代记录（批量）。
        
        Args:
            model_class: 模型类
            batch_size: 每批大小
            
        Yields:
            记录批次
        """
        pass
    
    @abstractmethod
    def cleanup_large_dataset(self, scenario: str):
        """清理大数据集测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Tuple, Type, Dict, Any
import tracemalloc
import time
from rhosocial.activerecord import ActiveRecord

class MemoryProfiler:
    """内存分析器。"""
    
    def __init__(self):
        self.start_memory = 0
        self.current_memory = 0
        self.peak_memory = 0
        self.snapshots = []
    
    def start(self):
        """开始内存监控。"""
        tracemalloc.start()
        self.start_memory = tracemalloc.get_traced_memory()[0]
        self.snapshots.clear()
    
    def snapshot(self, label: str = ""):
        """记录内存快照。"""
        current, peak = tracemalloc.get_traced_memory()
        self.snapshots.append({
            'label': label,
            'current': current,
            'peak': peak,
            'time': time.time()
        })
    
    def stop(self):
        """停止内存监控。"""
        self.current_memory, self.peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    
    def get_usage(self) -> Dict[str, int]:
        """获取内存使用情况（字节）。"""
        return {
            'start': self.start_memory,
            'current': self.current_memory,
            'peak': self.peak_memory,
            'used': self.current_memory - self.start_memory,
            'snapshots': self.snapshots
        }
    
    def print_report(self):
        """打印内存使用报告。"""
        usage = self.get_usage()
        print(f"\nMemory Usage Report:")
        print(f"  Start: {usage['start'] / 1024 / 1024:.2f} MB")
        print(f"  Current: {usage['current'] / 1024 / 1024:.2f} MB")
        print(f"  Peak: {usage['peak'] / 1024 / 1024:.2f} MB")
        print(f"  Used: {usage['used'] / 1024 / 1024:.2f} MB")
        
        if self.snapshots:
            print(f"\n  Snapshots:")
            for snap in self.snapshots:
                print(f"    {snap['label']:20s}: "
                      f"{snap['current'] / 1024 / 1024:.2f} MB")


@pytest.fixture
def large_dataset_models(request) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
    """
    提供大数据集测试模型。
    
    Returns:
        (LargeRecord, MediumRecord)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("large_resultset_benchmark_provider")
    
    models = provider.setup_large_dataset_models(scenario)
    
    yield models
    
    provider.cleanup_large_dataset(scenario)


@pytest.fixture
def memory_profiler(request):
    """提供内存分析器。"""
    provider = request.getfixturevalue("large_resultset_benchmark_provider")
    profiler = provider.get_memory_profiler()
    
    yield profiler


@pytest.fixture
def dataset_sizes():
    """提供测试的数据集大小配置。"""
    return {
        'tiny': 100,
        'small': 1000,
        'medium': 10000,
        'large': 100000,
        'xlarge': 1000000
    }
```

---

## 4. 测试类和函数签名

### 4.1 结果集大小与内存关系

```python
import pytest
import time

@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.parametrize("size_name,record_count", [
    ("tiny", 100),
    ("small", 1000),
    ("medium", 10000),
    ("large", 100000)
])
class TestResultSetMemory:
    """测试结果集大小对内存的影响。"""
    
    def test_full_load_memory(
        self,
        large_dataset_models,
        memory_profiler,
        size_name,
        record_count
    ):
        """
        测试全量加载的内存使用。
        
        验证点：
        1. 加载所有记录到内存
        2. 测量总内存占用
        3. 计算每条记录的平均内存
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        # 填充数据
        provider = pytest.config.getoption("large_resultset_benchmark_provider")
        provider.populate_large_dataset(record_count, LargeRecord)
        
        # 开始内存监控
        memory_profiler.start()
        memory_profiler.snapshot("before_query")
        
        # 全量加载
        start_time = time.time()
        records = LargeRecord.all()
        memory_profiler.snapshot("after_query")
        
        # 访问数据（确保物化）
        count = len(records)
        memory_profiler.snapshot("after_access")
        
        load_time = time.time() - start_time
        
        # 停止监控
        memory_profiler.stop()
        
        usage = memory_profiler.get_usage()
        memory_per_record = usage['used'] / count if count > 0 else 0
        
        print(f"\n{size_name.upper()} Dataset ({record_count} records):")
        print(f"  Load time: {load_time:.4f}s")
        print(f"  Total memory: {usage['used'] / 1024 / 1024:.2f} MB")
        print(f"  Memory per record: {memory_per_record / 1024:.2f} KB")
        print(f"  Peak memory: {usage['peak'] / 1024 / 1024:.2f} MB")
        
        # 验证线性增长
        assert count == record_count
    
    def test_memory_growth_pattern(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试内存增长模式。
        
        验证点：
        1. 内存增长是否线性
        2. 是否有内存泄漏
        3. 内存峰值出现时机
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        sizes = [100, 500, 1000, 5000, 10000]
        results = []
        
        for size in sizes:
            # 清理旧数据
            LargeRecord.delete_all()
            
            # 填充数据
            provider = pytest.config.getoption("large_resultset_benchmark_provider")
            provider.populate_large_dataset(size, LargeRecord)
            
            # 测量内存
            memory_profiler.start()
            records = LargeRecord.all()
            _ = len(records)
            memory_profiler.stop()
            
            usage = memory_profiler.get_usage()
            
            results.append({
                'size': size,
                'memory_mb': usage['used'] / 1024 / 1024,
                'memory_per_record_kb': usage['used'] / size / 1024
            })
            
            print(f"Size: {size:6d}, "
                  f"Memory: {usage['used'] / 1024 / 1024:6.2f} MB, "
                  f"Per record: {usage['used'] / size / 1024:.2f} KB")
        
        # 分析线性度
        if len(results) >= 2:
            # 简单线性回归分析
            avg_per_record = sum(r['memory_per_record_kb'] for r in results) / len(results)
            variance = sum((r['memory_per_record_kb'] - avg_per_record) ** 2 for r in results)
            std_dev = (variance / len(results)) ** 0.5
            coefficient_of_variation = (std_dev / avg_per_record * 100) if avg_per_record > 0 else 0
            
            print(f"\nMemory Growth Analysis:")
            print(f"  Avg per record: {avg_per_record:.2f} KB")
            print(f"  Std deviation: {std_dev:.2f} KB")
            print(f"  CV: {coefficient_of_variation:.2f}%")
            
            # 线性增长的 CV 应该较小（< 10%）
            assert coefficient_of_variation < 15


### 4.2 分页 vs 全量查询

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.large_scale
class TestPaginationVsFullLoad:
    """测试分页查询与全量查询的对比。"""
    
    def test_full_load_baseline(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试全量加载基准。
        
        验证点：
        1. 全量查询的内存峰值
        2. 加载时间
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 50000
        provider = pytest.config.getoption("large_resultset_benchmark_provider")
        provider.populate_large_dataset(record_count, LargeRecord)
        
        memory_profiler.start()
        start_time = time.time()
        
        records = LargeRecord.all()
        processed = sum(1 for r in records)
        
        load_time = time.time() - start_time
        memory_profiler.stop()
        
        usage = memory_profiler.get_usage()
        
        print(f"\nFull Load:")
        print(f"  Records: {processed}")
        print(f"  Time: {load_time:.4f}s")
        print(f"  Peak memory: {usage['peak'] / 1024 / 1024:.2f} MB")
        
        return {
            'time': load_time,
            'peak_memory': usage['peak'],
            'count': processed
        }
    
    def test_paginated_load(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试分页加载。
        
        验证点：
        1. 分页查询的内存控制
        2. 总时间（可能更长）
        3. 内存峰值（应该更低）
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 50000
        page_size = 1000
        
        memory_profiler.start()
        start_time = time.time()
        
        processed = 0
        page = 0
        
        while True:
            records = LargeRecord.limit(page_size).offset(page * page_size).all()
            if not records:
                break
            
            processed += len(records)
            page += 1
            
            memory_profiler.snapshot(f"page_{page}")
        
        load_time = time.time() - start_time
        memory_profiler.stop()
        
        usage = memory_profiler.get_usage()
        
        print(f"\nPaginated Load (page_size={page_size}):")
        print(f"  Records: {processed}")
        print(f"  Pages: {page}")
        print(f"  Time: {load_time:.4f}s")
        print(f"  Peak memory: {usage['peak'] / 1024 / 1024:.2f} MB")
        
        # 打印每页内存快照
        if usage['snapshots']:
            print(f"  Memory per page:")
            for snap in usage['snapshots'][:5]:  # 只打印前5页
                print(f"    {snap['label']}: {snap['current'] / 1024 / 1024:.2f} MB")
        
        return {
            'time': load_time,
            'peak_memory': usage['peak'],
            'count': processed,
            'pages': page
        }
    
    def test_pagination_memory_comparison(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        对比不同分页大小的内存使用。
        
        验证点：
        1. 最优分页大小
        2. 内存与时间的权衡
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 10000
        page_sizes = [100, 500, 1000, 2000, 5000]
        results = []
        
        for page_size in page_sizes:
            memory_profiler.start()
            start_time = time.time()
            
            processed = 0
            page = 0
            
            while True:
                records = LargeRecord.limit(page_size).offset(page * page_size).all()
                if not records:
                    break
                processed += len(records)
                page += 1
            
            elapsed = time.time() - start_time
            memory_profiler.stop()
            
            usage = memory_profiler.get_usage()
            
            results.append({
                'page_size': page_size,
                'time': elapsed,
                'peak_memory_mb': usage['peak'] / 1024 / 1024,
                'pages': page
            })
            
            print(f"Page size: {page_size:5d}, "
                  f"Time: {elapsed:.4f}s, "
                  f"Peak: {usage['peak'] / 1024 / 1024:.2f} MB, "
                  f"Pages: {page}")


### 4.3 流式处理

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.large_scale
class TestStreamingProcessing:
    """测试流式处理。"""
    
    def test_streaming_vs_materialization(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试流式处理 vs 完全物化。
        
        验证点：
        1. 流式处理的内存优势
        2. 性能对比
        3. 适用场景
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 20000
        provider = pytest.config.getoption("large_resultset_benchmark_provider")
        provider.populate_large_dataset(record_count, LargeRecord)
        
        # 检查是否支持流式处理
        if not provider.supports_streaming():
            pytest.skip("Backend does not support streaming")
        
        # 1. 完全物化
        memory_profiler.start()
        start_time = time.time()
        
        records = LargeRecord.all()
        materialized_count = 0
        for record in records:
            materialized_count += 1
            # 处理记录
        
        materialized_time = time.time() - start_time
        memory_profiler.stop()
        materialized_usage = memory_profiler.get_usage()
        
        # 2. 流式处理
        memory_profiler.start()
        start_time = time.time()
        
        streaming_count = 0
        for batch in provider.iterate_records(LargeRecord, batch_size=1000):
            for record in batch:
                streaming_count += 1
                # 处理记录
        
        streaming_time = time.time() - start_time
        memory_profiler.stop()
        streaming_usage = memory_profiler.get_usage()
        
        print(f"\nMaterialized:")
        print(f"  Count: {materialized_count}")
        print(f"  Time: {materialized_time:.4f}s")
        print(f"  Peak memory: {materialized_usage['peak'] / 1024 / 1024:.2f} MB")
        
        print(f"\nStreaming:")
        print(f"  Count: {streaming_count}")
        print(f"  Time: {streaming_time:.4f}s")
        print(f"  Peak memory: {streaming_usage['peak'] / 1024 / 1024:.2f} MB")
        
        memory_saving = (
            (materialized_usage['peak'] - streaming_usage['peak']) / 
            materialized_usage['peak'] * 100
        )
        print(f"\nMemory saving: {memory_saving:.1f}%")
    
    def test_streaming_batch_size(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试流式处理的批量大小影响。
        
        验证点：
        1. 批量大小对内存的影响
        2. 批量大小对性能的影响
        3. 最优批量大小
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 10000
        batch_sizes = [100, 500, 1000, 2000]
        
        provider = pytest.config.getoption("large_resultset_benchmark_provider")
        if not provider.supports_streaming():
            pytest.skip("Backend does not support streaming")
        
        results = []
        
        for batch_size in batch_sizes:
            memory_profiler.start()
            start_time = time.time()
            
            count = 0
            for batch in provider.iterate_records(LargeRecord, batch_size=batch_size):
                count += len(batch)
            
            elapsed = time.time() - start_time
            memory_profiler.stop()
            
            usage = memory_profiler.get_usage()
            
            results.append({
                'batch_size': batch_size,
                'time': elapsed,
                'peak_memory_mb': usage['peak'] / 1024 / 1024
            })
            
            print(f"Batch size: {batch_size:5d}, "
                  f"Time: {elapsed:.4f}s, "
                  f"Peak: {usage['peak'] / 1024 / 1024:.2f} MB")


### 4.4 内存泄漏检测

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.medium_scale
class TestMemoryLeaks:
    """测试内存泄漏。"""
    
    def test_repeated_queries_memory(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试重复查询是否导致内存泄漏。
        
        验证点：
        1. 多次查询后内存是否持续增长
        2. 垃圾回收是否有效
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 1000
        iterations = 10
        
        provider = pytest.config.getoption("large_resultset_benchmark_provider")
        provider.populate_large_dataset(record_count, LargeRecord)
        
        memory_samples = []
        
        for i in range(iterations):
            memory_profiler.start()
            
            # 执行查询
            records = LargeRecord.all()
            _ = len(records)
            
            # 显式触发垃圾回收
            import gc
            gc.collect()
            
            memory_profiler.stop()
            usage = memory_profiler.get_usage()
            
            memory_samples.append(usage['current'])
            
            print(f"Iteration {i+1}: {usage['current'] / 1024 / 1024:.2f} MB")
        
        # 分析内存趋势
        # 如果有明显增长趋势，可能存在泄漏
        first_half_avg = sum(memory_samples[:iterations//2]) / (iterations//2)
        second_half_avg = sum(memory_samples[iterations//2:]) / (iterations - iterations//2)
        
        growth_rate = (second_half_avg - first_half_avg) / first_half_avg * 100
        
        print(f"\nMemory growth rate: {growth_rate:.2f}%")
        
        # 合理的增长应该 < 10%
        assert growth_rate < 15, f"Potential memory leak detected: {growth_rate:.2f}% growth"


### 4.5 字段数量影响

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestFieldCountImpact:
    """测试字段数量对内存的影响。"""
    
    def test_many_fields_vs_few_fields(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        测试字段数量对内存使用的影响。
        
        验证点：
        1. 更多字段 = 更多内存
        2. 内存增长是否线性
        """
        LargeRecord, MediumRecord = large_dataset_models
        
        record_count = 5000
        
        # 测试 LargeRecord（更多字段）
        provider = pytest.config.getoption("large_resultset_benchmark_provider")
        provider.populate_large_dataset(record_count, LargeRecord)
        
        memory_profiler.start()
        large_records = LargeRecord.all()
        _ = len(large_records)
        memory_profiler.stop()
        
        large_usage = memory_profiler.get_usage()
        
        # 清理
        LargeRecord.delete_all()
        
        # 测试 MediumRecord（较少字段）
        provider.populate_large_dataset(record_count, MediumRecord)
        
        memory_profiler.start()
        medium_records = MediumRecord.all()
        _ = len(medium_records)
        memory_profiler.stop()
        
        medium_usage = memory_profiler.get_usage()
        
        print(f"\nLarge Record (many fields):")
        print(f"  Memory: {large_usage['used'] / 1024 / 1024:.2f} MB")
        print(f"  Per record: {large_usage['used'] / record_count / 1024:.2f} KB")
        
        print(f"\nMedium Record (fewer fields):")
        print(f"  Memory: {medium_usage['used'] / 1024 / 1024:.2f} MB")
        print(f"  Per record: {medium_usage['used'] / record_count / 1024:.2f} KB")
        
        ratio = large_usage['used'] / medium_usage['used'] if medium_usage['used'] > 0 else 0
        print(f"\nMemory ratio (Large/Medium): {ratio:.2f}x")


### 4.6 OOM 阈值测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.slow
class TestOOMThreshold:
    """测试内存溢出阈值（慎用）。"""
    
    def test_find_oom_threshold(
        self,
        large_dataset_models,
        memory_profiler
    ):
        """
        查找 OOM 阈值（谨慎执行）。
        
        验证点：
        1. 最大可处理的记录数
        2. 内存限制
        
        警告：此测试可能导致系统不稳定
        """
        pytest.skip("OOM test disabled by default")
        
        # 如果需要执行，取消上面的 skip
        
        LargeRecord, MediumRecord = large_dataset_models
        
        # 逐步增加数据量，直到 OOM
        sizes = [10000, 50000, 100000, 500000, 1000000]
        
        for size in sizes:
            try:
                print(f"\nTrying size: {size}")
                
                provider = pytest.config.getoption("large_resultset_benchmark_provider")
                provider.populate_large_dataset(size, LargeRecord)
                
                memory_profiler.start()
                records = LargeRecord.all()
                count = len(records)
                memory_profiler.stop()
                
                usage = memory_profiler.get_usage()
                
                print(f"  Success: {count} records loaded")
                print(f"  Memory: {usage['peak'] / 1024 / 1024:.2f} MB")
                
                # 清理
                LargeRecord.delete_all()
                
            except MemoryError:
                print(f"  OOM at {size} records")
                break
            except Exception as e:
                print(f"  Error at {size}: {e}")
                break
```

---

## 5. 性能基准目标

### 5.1 内存效率
- **每条记录**: < 1 KB overhead（相对于数据大小）
- **内存增长**: 线性（CV < 10%）
- **无泄漏**: 重复查询内存增长 < 10%

### 5.2 分页优化
- **内存节省**: 分页比全量节省 50-80% 内存
- **时间开销**: 分页时间不超过全量的 2x

### 5.3 流式处理
- **内存节省**: 相比物化节省 60-90% 内存
- **时间开销**: 时间增加 < 20%

---

## 6. 测试数据规模

### 6.1 Small Scale (< 10K)
- 验证基本功能
- 内存模式分析

### 6.2 Medium Scale (10K-100K)
- 常见业务场景
- 性能优化验证

### 6.3 Large Scale (100K-1M)
- 压力测试
- 扩展性验证

### 6.4 XLarge Scale (> 1M)
- 极限测试（谨慎）
- OOM 阈值探测

---

## 7. 实施注意事项

### 7.1 测试环境
- 足够的系统内存
- 监控系统资源
- 准备 OOM 恢复机制

### 7.2 内存测量
- 使用 tracemalloc 精确测量
- 考虑 Python 对象开销
- 区分 RSS 和 heap 内存

### 7.3 最佳实践
- 使用分页处理大数据
- 考虑流式处理
- 及时释放不需要的引用
- 定期垃圾回收

---

本实施方案提供了大结果集基准测试的完整框架。