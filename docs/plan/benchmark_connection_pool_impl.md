# 内存规模基准：连接池测试实施方案

## 1. 测试目标

本测试套件评估数据库连接池的性能和资源管理效率。连接池是提高数据库应用性能的关键组件，能够显著减少连接创建开销。

**核心验证点：**
- 单连接 vs 连接池的性能对比
- 不同池大小的吞吐量
- 连接获取和释放的时间
- 连接复用效率
- 池饱和时的行为
- 连接泄漏检测

**业务价值：**
- 优化连接池配置
- 提高应用吞吐量
- 减少资源浪费
- 提升系统稳定性

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, Dict, Any
from rhosocial.activerecord import ActiveRecord

class IConnectionPoolBenchmarkProvider(ABC):
    """连接池基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_pool_test_models(self, scenario: str) -> Type[ActiveRecord]:
        """
        设置连接池测试模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            测试模型类
        """
        pass
    
    @abstractmethod
    def create_connection_pool(
        self,
        pool_size: int,
        max_overflow: int = 0,
        pool_timeout: float = 30.0
    ) -> 'ConnectionPool':
        """
        创建连接池。
        
        Args:
            pool_size: 池大小
            max_overflow: 最大溢出连接数
            pool_timeout: 连接获取超时（秒）
            
        Returns:
            连接池对象
        """
        pass
    
    @abstractmethod
    def get_pool_statistics(self) -> Dict[str, Any]:
        """
        获取连接池统计信息。
        
        Returns:
            包含池状态、连接数、等待数等统计
        """
        pass
    
    @abstractmethod
    def reset_pool(self):
        """重置连接池（清理所有连接）。"""
        pass
    
    @abstractmethod
    def get_connection_creation_time(self) -> float:
        """
        测量创建单个连接的时间。
        
        Returns:
            连接创建时间（秒）
        """
        pass
    
    @abstractmethod
    def cleanup_pool_test(self, scenario: str):
        """清理连接池测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Type, Dict, Any
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from rhosocial.activerecord import ActiveRecord

class ConnectionPoolMetrics:
    """连接池性能指标收集器。"""
    
    def __init__(self):
        self.connection_waits = []
        self.connection_acquisitions = 0
        self.connection_releases = 0
        self.timeouts = 0
        self.errors = 0
        self.lock = threading.Lock()
    
    def record_acquisition(self, wait_time: float):
        """记录连接获取。"""
        with self.lock:
            self.connection_acquisitions += 1
            self.connection_waits.append(wait_time)
    
    def record_release(self):
        """记录连接释放。"""
        with self.lock:
            self.connection_releases += 1
    
    def record_timeout(self):
        """记录超时。"""
        with self.lock:
            self.timeouts += 1
    
    def record_error(self):
        """记录错误。"""
        with self.lock:
            self.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。"""
        with self.lock:
            avg_wait = (
                sum(self.connection_waits) / len(self.connection_waits)
                if self.connection_waits else 0
            )
            max_wait = max(self.connection_waits) if self.connection_waits else 0
            
            return {
                'acquisitions': self.connection_acquisitions,
                'releases': self.connection_releases,
                'avg_wait': avg_wait,
                'max_wait': max_wait,
                'timeouts': self.timeouts,
                'errors': self.errors,
                'leak_count': self.connection_acquisitions - self.connection_releases
            }


@pytest.fixture
def pool_test_model(request) -> Type[ActiveRecord]:
    """
    提供连接池测试模型。
    
    Returns:
        测试模型类
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("connection_pool_benchmark_provider")
    
    model = provider.setup_pool_test_models(scenario)
    
    yield model
    
    provider.cleanup_pool_test(scenario)


@pytest.fixture
def pool_metrics():
    """提供连接池指标收集器。"""
    return ConnectionPoolMetrics()


@pytest.fixture
def connection_pool(request):
    """提供可配置的连接池。"""
    provider = request.getfixturevalue("connection_pool_benchmark_provider")
    
    # 默认配置
    pool_size = 10
    max_overflow = 5
    
    pool = provider.create_connection_pool(
        pool_size=pool_size,
        max_overflow=max_overflow
    )
    
    yield pool
    
    # 清理
    provider.reset_pool()
```

---

## 4. 测试类和函数签名

### 4.1 单连接基准

```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestSingleConnectionBaseline:
    """测试单连接基准（无连接池）。"""
    
    def test_single_connection_throughput(
        self,
        pool_test_model
    ):
        """
        测试单连接的吞吐量。
        
        验证点：
        1. 无连接池的基准性能
        2. 连接创建开销
        """
        Model = pool_test_model
        
        queries = 100
        
        start_time = time.time()
        
        for i in range(queries):
            # 每次查询创建新连接（模拟无连接池）
            record = Model(name=f"test_{i}", value=i)
            record.save()
        
        elapsed = time.time() - start_time
        throughput = queries / elapsed
        
        print(f"\nSingle Connection (no pool):")
        print(f"  Queries: {queries}")
        print(f"  Time: {elapsed:.4f}s")
        print(f"  Throughput: {throughput:.0f} queries/s")
        
        return throughput
    
    def test_connection_creation_overhead(
        self,
        pool_test_model
    ):
        """
        测量连接创建的开销。
        
        验证点：
        1. 单次连接创建时间
        2. 平均创建时间
        """
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        iterations = 10
        times = []
        
        for _ in range(iterations):
            creation_time = provider.get_connection_creation_time()
            times.append(creation_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\nConnection Creation Time:")
        print(f"  Average: {avg_time * 1000:.2f}ms")
        print(f"  Min: {min_time * 1000:.2f}ms")
        print(f"  Max: {max_time * 1000:.2f}ms")


### 4.2 连接池大小优化

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.medium_scale
class TestPoolSizeOptimization:
    """测试不同连接池大小的性能。"""
    
    def test_various_pool_sizes(
        self,
        pool_test_model
    ):
        """
        测试不同池大小的吞吐量。
        
        验证点：
        1. 池大小对性能的影响
        2. 最优池大小
        3. 边际效应
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        pool_sizes = [1, 5, 10, 20, 50]
        num_threads = 20
        queries_per_thread = 50
        results = []
        
        for pool_size in pool_sizes:
            # 创建连接池
            pool = provider.create_connection_pool(pool_size=pool_size)
            
            def worker():
                """工作线程：执行查询。"""
                for i in range(queries_per_thread):
                    record = Model(name=f"test_{i}", value=i)
                    record.save()
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker) for _ in range(num_threads)]
                for future in as_completed(futures):
                    future.result()
            
            elapsed = time.time() - start_time
            total_queries = num_threads * queries_per_thread
            throughput = total_queries / elapsed
            
            results.append({
                'pool_size': pool_size,
                'time': elapsed,
                'throughput': throughput
            })
            
            print(f"Pool size: {pool_size:3d}, "
                  f"Time: {elapsed:.4f}s, "
                  f"Throughput: {throughput:.0f} queries/s")
            
            # 重置连接池
            provider.reset_pool()
        
        # 找到最优池大小
        best = max(results, key=lambda x: x['throughput'])
        print(f"\nOptimal pool size: {best['pool_size']} "
              f"({best['throughput']:.0f} queries/s)")
    
    def test_pool_size_vs_threads(
        self,
        pool_test_model
    ):
        """
        测试池大小与线程数的关系。
        
        验证点：
        1. 池大小 >= 线程数时的性能
        2. 池大小 < 线程数时的等待
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        thread_counts = [5, 10, 20]
        
        for num_threads in thread_counts:
            print(f"\nThread count: {num_threads}")
            
            # 池大小 = 线程数的一半（不足）
            pool_size = num_threads // 2
            pool = provider.create_connection_pool(pool_size=pool_size)
            
            def worker():
                for _ in range(20):
                    record = Model(name="test", value=1)
                    record.save()
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker) for _ in range(num_threads)]
                for future in as_completed(futures):
                    future.result()
            insufficient_time = time.time() - start_time
            
            # 重置
            provider.reset_pool()
            
            # 池大小 = 线程数（充足）
            pool = provider.create_connection_pool(pool_size=num_threads)
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker) for _ in range(num_threads)]
                for future in as_completed(futures):
                    future.result()
            sufficient_time = time.time() - start_time
            
            improvement = (insufficient_time - sufficient_time) / insufficient_time * 100
            
            print(f"  Pool={pool_size:2d}: {insufficient_time:.4f}s")
            print(f"  Pool={num_threads:2d}: {sufficient_time:.4f}s")
            print(f"  Improvement: {improvement:.1f}%")
            
            provider.reset_pool()


### 4.3 连接复用效率

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestConnectionReuse:
    """测试连接复用效率。"""
    
    def test_connection_reuse_rate(
        self,
        pool_test_model,
        pool_metrics
    ):
        """
        测试连接复用率。
        
        验证点：
        1. 连接获取和释放次数
        2. 复用率
        3. 池效率
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        pool_size = 5
        pool = provider.create_connection_pool(pool_size=pool_size)
        
        num_operations = 100
        
        for i in range(num_operations):
            start_wait = time.time()
            
            # 执行操作（获取连接）
            record = Model(name=f"test_{i}", value=i)
            record.save()
            
            wait_time = time.time() - start_wait
            pool_metrics.record_acquisition(wait_time)
            pool_metrics.record_release()
        
        stats = pool_metrics.get_stats()
        pool_stats = provider.get_pool_statistics()
        
        reuse_rate = (stats['acquisitions'] - pool_size) / stats['acquisitions'] * 100
        
        print(f"\nConnection Reuse:")
        print(f"  Pool size: {pool_size}")
        print(f"  Operations: {num_operations}")
        print(f"  Acquisitions: {stats['acquisitions']}")
        print(f"  Releases: {stats['releases']}")
        print(f"  Reuse rate: {reuse_rate:.1f}%")
        print(f"  Avg wait: {stats['avg_wait'] * 1000:.2f}ms")
        
        if 'created_connections' in pool_stats:
            print(f"  Connections created: {pool_stats['created_connections']}")
    
    def test_connection_lifetime(
        self,
        pool_test_model
    ):
        """
        测试连接的生命周期。
        
        验证点：
        1. 连接在池中的存活时间
        2. 连接的复用次数
        """
        # 如果后端支持连接生命周期跟踪
        pass


### 4.4 池饱和处理

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.medium_scale
class TestPoolSaturation:
    """测试连接池饱和情况。"""
    
    def test_pool_exhaustion_behavior(
        self,
        pool_test_model,
        pool_metrics
    ):
        """
        测试池耗尽时的行为。
        
        验证点：
        1. 等待可用连接
        2. 超时处理
        3. 错误恢复
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        pool_size = 5
        max_overflow = 0  # 不允许溢出
        pool_timeout = 2.0  # 2秒超时
        
        pool = provider.create_connection_pool(
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout
        )
        
        num_threads = 10  # 超过池大小
        
        def worker(worker_id):
            """工作线程：持有连接一段时间。"""
            try:
                start_wait = time.time()
                
                # 获取连接并执行查询
                record = Model(name=f"test_{worker_id}", value=worker_id)
                record.save()
                
                wait_time = time.time() - start_wait
                pool_metrics.record_acquisition(wait_time)
                
                # 模拟长时间操作
                time.sleep(0.5)
                
                pool_metrics.record_release()
                
            except Exception as e:
                if 'timeout' in str(e).lower():
                    pool_metrics.record_timeout()
                else:
                    pool_metrics.record_error()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
        
        stats = pool_metrics.get_stats()
        
        print(f"\nPool Saturation Test:")
        print(f"  Pool size: {pool_size}")
        print(f"  Threads: {num_threads}")
        print(f"  Successful acquisitions: {stats['acquisitions']}")
        print(f"  Timeouts: {stats['timeouts']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Max wait: {stats['max_wait'] * 1000:.2f}ms")
    
    def test_overflow_connections(
        self,
        pool_test_model,
        pool_metrics
    ):
        """
        测试溢出连接。
        
        验证点：
        1. 溢出连接的创建
        2. 溢出连接的释放
        3. 性能影响
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        pool_size = 5
        max_overflow = 5  # 允许5个溢出连接
        
        pool = provider.create_connection_pool(
            pool_size=pool_size,
            max_overflow=max_overflow
        )
        
        num_threads = pool_size + max_overflow
        
        def worker():
            for _ in range(10):
                record = Model(name="test", value=1)
                record.save()
                pool_metrics.record_acquisition(0)
                pool_metrics.record_release()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        
        pool_stats = provider.get_pool_statistics()
        
        print(f"\nOverflow Connections Test:")
        print(f"  Pool size: {pool_size}")
        print(f"  Max overflow: {max_overflow}")
        print(f"  Total available: {pool_size + max_overflow}")
        print(f"  Time: {elapsed:.4f}s")
        
        if 'overflow_used' in pool_stats:
            print(f"  Overflow connections used: {pool_stats['overflow_used']}")


### 4.5 连接泄漏检测

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.small_scale
class TestConnectionLeaks:
    """测试连接泄漏检测。"""
    
    def test_connection_leak_detection(
        self,
        pool_test_model,
        pool_metrics
    ):
        """
        测试连接泄漏检测。
        
        验证点：
        1. 未释放的连接
        2. 泄漏警告
        3. 池状态
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        pool_size = 5
        pool = provider.create_connection_pool(pool_size=pool_size)
        
        # 正常操作
        for i in range(10):
            record = Model(name=f"test_{i}", value=i)
            record.save()
            pool_metrics.record_acquisition(0)
            pool_metrics.record_release()
        
        # 模拟泄漏（如果可能）
        # 某些操作未释放连接
        
        stats = pool_metrics.get_stats()
        
        if stats['leak_count'] > 0:
            print(f"\nConnection Leak Detected:")
            print(f"  Leaked connections: {stats['leak_count']}")
        else:
            print(f"\nNo Connection Leaks")
        
        assert stats['leak_count'] == 0, f"Connection leak: {stats['leak_count']} connections"


### 4.6 并发性能

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_scale
@pytest.mark.medium_scale
class TestPoolConcurrency:
    """测试连接池的并发性能。"""
    
    def test_concurrent_throughput(
        self,
        pool_test_model
    ):
        """
        测试并发场景下的吞吐量。
        
        验证点：
        1. 多线程并发查询
        2. 连接池效率
        3. 与单连接对比
        """
        Model = pool_test_model
        provider = pytest.config.getoption("connection_pool_benchmark_provider")
        
        pool_size = 10
        num_threads = 20
        queries_per_thread = 100
        
        # 使用连接池
        pool = provider.create_connection_pool(pool_size=pool_size)
        
        def worker():
            for i in range(queries_per_thread):
                record = Model(name=f"test_{i}", value=i)
                record.save()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        total_queries = num_threads * queries_per_thread
        throughput = total_queries / elapsed
        
        print(f"\nConcurrent Throughput (pool_size={pool_size}):")
        print(f"  Threads: {num_threads}")
        print(f"  Total queries: {total_queries}")
        print(f"  Time: {elapsed:.4f}s")
        print(f"  Throughput: {throughput:.0f} queries/s")
        
        return throughput
```

---

## 5. 性能基准目标

### 5.1 连接池效率
- **复用率**: > 95%
- **等待时间**: 平均 < 1ms（池未饱和时）
- **吞吐量提升**: 相比单连接提升 5-10x

### 5.2 最优配置
- **池大小**: 通常 = 核心线程数
- **溢出连接**: 10-20% 的池大小
- **超时设置**: 10-30 秒

### 5.3 资源管理
- **连接泄漏**: 0
- **溢出使用率**: < 10%（正常负载）

---

## 6. 所需能力

```python
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    ConnectionCapability
)

optional_capabilities = [
    (CapabilityCategory.CONNECTION, ConnectionCapability.CONNECTION_POOLING),
    (CapabilityCategory.CONNECTION, ConnectionCapability.POOL_STATISTICS)
]
```

---

## 7. 实施注意事项

### 7.1 连接池配置
- 根据应用负载调整池大小
- 设置合理的超时时间
- 监控池统计信息

### 7.2 测试环境
- 模拟真实并发负载
- 控制数据库服务器负载
- 监控系统资源

### 7.3 最佳实践
- 及时释放连接
- 使用 try-finally 或上下文管理器
- 监控连接泄漏
- 定期检查池状态

---

本实施方案提供了连接池基准测试的完整框架。