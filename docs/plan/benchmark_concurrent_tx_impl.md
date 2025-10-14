# 事务性能基准：并发事务测试实施方案

## 1. 测试目标

本测试套件评估并发事务场景下的性能和正确性。并发事务是多用户系统的常见场景，需要在保证数据一致性的同时维持良好的性能。

**核心验证点：**
- 只读并发查询的吞吐量
- 写写冲突的处理性能
- 读写冲突的影响
- 不同隔离级别下的并发性能
- 锁等待时间统计
- 死锁频率和处理

**业务价值：**
- 评估系统的并发处理能力
- 识别并发瓶颈
- 优化锁策略
- 为容量规划提供数据

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict, Any, Callable
from rhosocial.activerecord import ActiveRecord
import threading

class IConcurrentTransactionBenchmarkProvider(ABC):
    """并发事务基准测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_concurrent_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # Account (账户)
        Type[ActiveRecord],  # Counter (计数器)
        Type[ActiveRecord]   # LockTest (锁测试)
    ]:
        """
        设置并发测试模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 3 个模型类的元组：
            - Account: 账户（测试写写冲突）
            - Counter: 计数器（测试并发更新）
            - LockTest: 锁测试记录
        """
        pass
    
    @abstractmethod
    def populate_concurrent_test_data(
        self,
        accounts: int = 100,
        initial_balance: float = 1000.0
    ) -> Dict[str, Any]:
        """
        填充并发测试数据。
        
        Args:
            accounts: 账户数量
            initial_balance: 初始余额
            
        Returns:
            包含统计信息的字典
        """
        pass
    
    @abstractmethod
    def create_thread_pool(self, size: int) -> 'ThreadPool':
        """
        创建线程池执行并发任务。
        
        Args:
            size: 线程池大小
            
        Returns:
            线程池对象
        """
        pass
    
    @abstractmethod
    def get_lock_statistics(self) -> Dict[str, Any]:
        """
        获取锁统计信息。
        
        Returns:
            包含锁等待时间、死锁次数等统计
        """
        pass
    
    @abstractmethod
    def get_transaction_context(self):
        """获取事务上下文管理器。"""
        pass
    
    @abstractmethod
    def set_isolation_level(self, level: str):
        """设置事务隔离级别。"""
        pass
    
    @abstractmethod
    def cleanup_concurrent_data(self, scenario: str):
        """清理并发测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Tuple, Type, Dict, Any, List
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from rhosocial.activerecord import ActiveRecord

class ConcurrentMetrics:
    """并发测试指标收集器。"""
    
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.lock_wait_times = []
        self.deadlock_count = 0
        self.total_time = 0.0
        self.lock = threading.Lock()
    
    def record_success(self, wait_time: float = 0):
        with self.lock:
            self.success_count += 1
            if wait_time > 0:
                self.lock_wait_times.append(wait_time)
    
    def record_failure(self, is_deadlock: bool = False):
        with self.lock:
            self.failure_count += 1
            if is_deadlock:
                self.deadlock_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            avg_wait = (
                sum(self.lock_wait_times) / len(self.lock_wait_times) 
                if self.lock_wait_times else 0
            )
            return {
                'success': self.success_count,
                'failure': self.failure_count,
                'deadlocks': self.deadlock_count,
                'avg_lock_wait': avg_wait,
                'max_lock_wait': max(self.lock_wait_times) if self.lock_wait_times else 0,
                'throughput': self.success_count / self.total_time if self.total_time > 0 else 0
            }


@pytest.fixture
def concurrent_models(request) -> Tuple[
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord]
]:
    """
    提供并发测试模型。
    
    Returns:
        (Account, Counter, LockTest)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("concurrent_transaction_benchmark_provider")
    
    models = provider.setup_concurrent_models(scenario)
    
    yield models
    
    provider.cleanup_concurrent_data(scenario)


@pytest.fixture
def concurrent_test_data(concurrent_models, request):
    """填充并发测试数据。"""
    provider = request.getfixturevalue("concurrent_transaction_benchmark_provider")
    
    markers = [m.name for m in request.node.iter_markers()]
    
    if 'small_scale' in markers:
        stats = provider.populate_concurrent_test_data(accounts=50, initial_balance=1000.0)
    elif 'medium_scale' in markers:
        stats = provider.populate_concurrent_test_data(accounts=200, initial_balance=1000.0)
    elif 'large_scale' in markers:
        stats = provider.populate_concurrent_test_data(accounts=1000, initial_balance=1000.0)
    else:
        stats = provider.populate_concurrent_test_data()
    
    yield stats


@pytest.fixture
def thread_pool(request):
    """提供线程池。"""
    provider = request.getfixturevalue("concurrent_transaction_benchmark_provider")
    
    # 默认线程池大小
    pool_size = 10
    
    pool = provider.create_thread_pool(pool_size)
    
    yield pool
    
    # 清理线程池
    pool.shutdown(wait=True)


@pytest.fixture
def concurrent_metrics():
    """提供并发指标收集器。"""
    return ConcurrentMetrics()


@pytest.fixture
def transaction_context(request):
    """提供事务上下文。"""
    provider = request.getfixturevalue("concurrent_transaction_benchmark_provider")
    return provider.get_transaction_context()


@pytest.fixture
def isolation_level_setter(request):
    """提供隔离级别设置函数。"""
    provider = request.getfixturevalue("concurrent_transaction_benchmark_provider")
    return provider.set_isolation_level
```

---

## 4. 测试类和函数签名

### 4.1 只读并发查询

```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.small_scale
class TestReadOnlyConcurrency:
    """测试只读并发查询的性能。"""
    
    def test_concurrent_read_queries(
        self,
        concurrent_models,
        concurrent_test_data,
        concurrent_metrics
    ):
        """
        测试并发读查询的吞吐量。
        
        验证点：
        1. 多线程同时读取数据
        2. 无锁冲突
        3. 吞吐量线性扩展
        """
        Account, Counter, LockTest = concurrent_models
        
        num_threads = 10
        queries_per_thread = 100
        
        def read_worker():
            """工作线程：执行读查询。"""
            for _ in range(queries_per_thread):
                accounts = Account.limit(10).all()
                concurrent_metrics.record_success()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(read_worker) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        concurrent_metrics.total_time = elapsed
        
        stats = concurrent_metrics.get_stats()
        
        print(f"Total queries: {stats['success']}")
        print(f"Time: {elapsed:.4f}s")
        print(f"Throughput: {stats['throughput']:.0f} queries/s")
    
    def test_read_scalability(
        self,
        concurrent_models,
        concurrent_test_data
    ):
        """
        测试读查询的可扩展性。
        
        验证点：
        1. 不同线程数的吞吐量
        2. 扩展性曲线
        """
        Account, Counter, LockTest = concurrent_models
        
        thread_counts = [1, 2, 5, 10, 20]
        queries_per_thread = 100
        results = []
        
        for num_threads in thread_counts:
            def read_worker():
                for _ in range(queries_per_thread):
                    Account.limit(10).all()
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(read_worker) for _ in range(num_threads)]
                for future in as_completed(futures):
                    future.result()
            
            elapsed = time.time() - start_time
            total_queries = num_threads * queries_per_thread
            throughput = total_queries / elapsed
            
            results.append({
                'threads': num_threads,
                'throughput': throughput,
                'time': elapsed
            })
            
            print(f"Threads: {num_threads}, Throughput: {throughput:.0f} queries/s")
        
        # 计算扩展性
        baseline = results[0]['throughput']
        for r in results:
            efficiency = r['throughput'] / (baseline * r['threads']) * 100
            print(f"  {r['threads']} threads: {efficiency:.1f}% efficiency")


### 4.2 写写冲突

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.small_scale
class TestWriteWriteConflicts:
    """测试写写冲突场景。"""
    
    def test_concurrent_updates_same_record(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        concurrent_metrics
    ):
        """
        测试多个事务更新同一记录。
        
        验证点：
        1. 锁等待时间
        2. 串行化执行
        3. 最终数据一致性
        """
        Account, Counter, LockTest = concurrent_models
        
        # 创建测试账户
        account = Account(name="test", balance=1000.0)
        account.save()
        
        num_threads = 10
        increment = 10.0
        
        def update_worker():
            """工作线程：更新同一账户。"""
            try:
                wait_start = time.time()
                with transaction_context:
                    acc = Account.find(account.id)
                    acc.balance += increment
                    acc.save()
                wait_time = time.time() - wait_start
                concurrent_metrics.record_success(wait_time)
            except Exception as e:
                concurrent_metrics.record_failure('deadlock' in str(e).lower())
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(update_worker) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        concurrent_metrics.total_time = elapsed
        
        # 验证最终余额
        final_account = Account.find(account.id)
        expected_balance = 1000.0 + (increment * concurrent_metrics.success_count)
        
        stats = concurrent_metrics.get_stats()
        
        print(f"Success: {stats['success']}, Failure: {stats['failure']}")
        print(f"Average lock wait: {stats['avg_lock_wait'] * 1000:.2f}ms")
        print(f"Max lock wait: {stats['max_lock_wait'] * 1000:.2f}ms")
        print(f"Final balance: {final_account.balance} (expected: {expected_balance})")
        
        assert abs(final_account.balance - expected_balance) < 0.01
    
    def test_concurrent_updates_different_records(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        concurrent_metrics
    ):
        """
        测试多个事务更新不同记录。
        
        验证点：
        1. 无锁冲突
        2. 并行执行
        3. 高吞吐量
        """
        Account, Counter, LockTest = concurrent_models
        
        # 创建多个账户
        accounts = [Account(name=f"acc_{i}", balance=1000.0) for i in range(100)]
        for acc in accounts:
            acc.save()
        
        num_threads = 10
        updates_per_thread = 10
        
        def update_worker(worker_id):
            """工作线程：更新不同账户。"""
            for i in range(updates_per_thread):
                account_idx = (worker_id * updates_per_thread + i) % len(accounts)
                try:
                    with transaction_context:
                        acc = Account.find(accounts[account_idx].id)
                        acc.balance += 10.0
                        acc.save()
                    concurrent_metrics.record_success()
                except Exception as e:
                    concurrent_metrics.record_failure()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(update_worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        concurrent_metrics.total_time = elapsed
        
        stats = concurrent_metrics.get_stats()
        
        print(f"Total updates: {stats['success']}")
        print(f"Time: {elapsed:.4f}s")
        print(f"Throughput: {stats['throughput']:.0f} updates/s")
        print(f"Avg lock wait: {stats['avg_lock_wait'] * 1000:.2f}ms")


### 4.3 读写冲突

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.medium_scale
class TestReadWriteConflicts:
    """测试读写冲突场景。"""
    
    def test_concurrent_read_and_write(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        concurrent_metrics
    ):
        """
        测试并发读写混合场景。
        
        验证点：
        1. 读操作不阻塞写操作（READ COMMITTED）
        2. 写操作可能阻塞读操作（取决于隔离级别）
        3. 混合负载的吞吐量
        """
        Account, Counter, LockTest = concurrent_models
        
        # 创建测试账户
        accounts = [Account(name=f"acc_{i}", balance=1000.0) for i in range(50)]
        for acc in accounts:
            acc.save()
        
        num_reader_threads = 5
        num_writer_threads = 5
        operations_per_thread = 20
        
        def reader_worker():
            """读线程。"""
            for _ in range(operations_per_thread):
                try:
                    with transaction_context:
                        accounts = Account.limit(10).all()
                        # 读取余额
                        _ = [acc.balance for acc in accounts]
                    concurrent_metrics.record_success()
                except Exception:
                    concurrent_metrics.record_failure()
        
        def writer_worker():
            """写线程。"""
            for i in range(operations_per_thread):
                account_idx = i % len(accounts)
                try:
                    with transaction_context:
                        acc = Account.find(accounts[account_idx].id)
                        acc.balance += 10.0
                        acc.save()
                    concurrent_metrics.record_success()
                except Exception:
                    concurrent_metrics.record_failure()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_reader_threads + num_writer_threads) as executor:
            reader_futures = [executor.submit(reader_worker) for _ in range(num_reader_threads)]
            writer_futures = [executor.submit(writer_worker) for _ in range(num_writer_threads)]
            
            for future in as_completed(reader_futures + writer_futures):
                future.result()
        
        elapsed = time.time() - start_time
        concurrent_metrics.total_time = elapsed
        
        stats = concurrent_metrics.get_stats()
        
        print(f"Total operations: {stats['success']}")
        print(f"Time: {elapsed:.4f}s")
        print(f"Throughput: {stats['throughput']:.0f} ops/s")


### 4.4 隔离级别影响

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.medium_scale
class TestIsolationLevelConcurrency:
    """测试不同隔离级别下的并发性能。"""
    
    def test_read_committed_concurrency(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        isolation_level_setter,
        concurrent_metrics
    ):
        """
        测试 READ COMMITTED 隔离级别。
        
        验证点：
        1. 读不阻塞写，写不阻塞读
        2. 允许不可重复读
        3. 较高的并发性能
        """
        isolation_level_setter('read_committed')
        
        Account, Counter, LockTest = concurrent_models
        
        # 执行并发测试
        # ... (类似上面的读写混合测试)
        
        stats = concurrent_metrics.get_stats()
        print(f"READ COMMITTED - Throughput: {stats['throughput']:.0f} ops/s")
        
        return stats['throughput']
    
    def test_repeatable_read_concurrency(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        isolation_level_setter,
        concurrent_metrics
    ):
        """
        测试 REPEATABLE READ 隔离级别。
        
        验证点：
        1. 防止不可重复读
        2. 可能降低并发性能
        3. 与 READ COMMITTED 对比
        """
        isolation_level_setter('repeatable_read')
        
        # 执行相同的并发测试
        # ...
        
        stats = concurrent_metrics.get_stats()
        print(f"REPEATABLE READ - Throughput: {stats['throughput']:.0f} ops/s")
        
        return stats['throughput']
    
    def test_serializable_concurrency(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        isolation_level_setter,
        concurrent_metrics
    ):
        """
        测试 SERIALIZABLE 隔离级别。
        
        验证点：
        1. 最严格的隔离
        2. 最低的并发性能
        3. 可能出现序列化失败
        """
        isolation_level_setter('serializable')
        
        # 执行相同的并发测试
        # ...
        
        stats = concurrent_metrics.get_stats()
        print(f"SERIALIZABLE - Throughput: {stats['throughput']:.0f} ops/s")
        print(f"Serialization failures: {stats['failure']}")
        
        return stats['throughput']


### 4.5 死锁检测和处理

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.small_scale
class TestDeadlockHandling:
    """测试死锁场景。"""
    
    def test_simple_deadlock(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        concurrent_metrics
    ):
        """
        测试简单的两个事务死锁。
        
        验证点：
        1. 死锁检测
        2. 死锁解决时间
        3. 重试机制
        """
        Account, Counter, LockTest = concurrent_models
        
        # 创建两个账户
        acc1 = Account(name="acc1", balance=1000.0)
        acc1.save()
        acc2 = Account(name="acc2", balance=1000.0)
        acc2.save()
        
        def transaction_1():
            """事务1: 锁定 acc1 -> acc2"""
            try:
                with transaction_context:
                    a1 = Account.find(acc1.id)
                    a1.balance += 10
                    a1.save()
                    
                    time.sleep(0.1)  # 等待事务2锁定 acc2
                    
                    a2 = Account.find(acc2.id)
                    a2.balance += 10
                    a2.save()
                
                concurrent_metrics.record_success()
            except Exception as e:
                is_deadlock = 'deadlock' in str(e).lower()
                concurrent_metrics.record_failure(is_deadlock)
        
        def transaction_2():
            """事务2: 锁定 acc2 -> acc1"""
            try:
                with transaction_context:
                    a2 = Account.find(acc2.id)
                    a2.balance += 10
                    a2.save()
                    
                    time.sleep(0.1)  # 等待事务1锁定 acc1
                    
                    a1 = Account.find(acc1.id)
                    a1.balance += 10
                    a1.save()
                
                concurrent_metrics.record_success()
            except Exception as e:
                is_deadlock = 'deadlock' in str(e).lower()
                concurrent_metrics.record_failure(is_deadlock)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(transaction_1)
            f2 = executor.submit(transaction_2)
            
            f1.result()
            f2.result()
        
        elapsed = time.time() - start_time
        
        stats = concurrent_metrics.get_stats()
        
        print(f"Deadlocks detected: {stats['deadlocks']}")
        print(f"Time to resolve: {elapsed:.4f}s")
        print(f"Success: {stats['success']}, Failure: {stats['failure']}")
    
    def test_deadlock_frequency(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        concurrent_metrics
    ):
        """
        测试高并发下的死锁频率。
        
        验证点：
        1. 死锁发生率
        2. 对吞吐量的影响
        3. 重试成功率
        """
        Account, Counter, LockTest = concurrent_models
        
        # 创建多个账户
        accounts = [Account(name=f"acc_{i}", balance=1000.0) for i in range(10)]
        for acc in accounts:
            acc.save()
        
        num_threads = 20
        operations_per_thread = 10
        
        def worker(worker_id):
            """工作线程：随机顺序更新两个账户。"""
            for i in range(operations_per_thread):
                # 随机选择两个账户
                import random
                idx1, idx2 = random.sample(range(len(accounts)), 2)
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with transaction_context:
                            acc1 = Account.find(accounts[idx1].id)
                            acc1.balance += 10
                            acc1.save()
                            
                            time.sleep(0.001)  # 增加冲突概率
                            
                            acc2 = Account.find(accounts[idx2].id)
                            acc2.balance -= 10
                            acc2.save()
                        
                        concurrent_metrics.record_success()
                        break
                    except Exception as e:
                        is_deadlock = 'deadlock' in str(e).lower()
                        if attempt == max_retries - 1:
                            concurrent_metrics.record_failure(is_deadlock)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        concurrent_metrics.total_time = elapsed
        
        stats = concurrent_metrics.get_stats()
        
        total_attempts = num_threads * operations_per_thread
        deadlock_rate = stats['deadlocks'] / total_attempts * 100
        
        print(f"Total attempts: {total_attempts}")
        print(f"Deadlocks: {stats['deadlocks']} ({deadlock_rate:.2f}%)")
        print(f"Success: {stats['success']}")
        print(f"Throughput: {stats['throughput']:.0f} ops/s")


### 4.6 锁等待时间分析

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.medium_scale
class TestLockWaitAnalysis:
    """测试锁等待时间分析。"""
    
    def test_lock_wait_distribution(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context,
        concurrent_metrics
    ):
        """
        测试锁等待时间分布。
        
        验证点：
        1. 锁等待时间的分布情况
        2. 平均、最大、P95 等待时间
        3. 识别锁竞争热点
        """
        Account, Counter, LockTest = concurrent_models
        
        # 创建热点账户（多个线程竞争）
        hotspot = Account(name="hotspot", balance=10000.0)
        hotspot.save()
        
        num_threads = 20
        updates_per_thread = 10
        
        def worker():
            """工作线程：更新热点账户。"""
            for _ in range(updates_per_thread):
                wait_start = time.time()
                try:
                    with transaction_context:
                        acc = Account.find(hotspot.id)
                        acc.balance += 1.0
                        acc.save()
                    wait_time = time.time() - wait_start
                    concurrent_metrics.record_success(wait_time)
                except Exception:
                    concurrent_metrics.record_failure()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        
        stats = concurrent_metrics.get_stats()
        
        # 计算百分位数
        wait_times = sorted(concurrent_metrics.lock_wait_times)
        if wait_times:
            p50 = wait_times[len(wait_times) // 2]
            p95 = wait_times[int(len(wait_times) * 0.95)]
            p99 = wait_times[int(len(wait_times) * 0.99)]
            
            print(f"Lock wait time statistics:")
            print(f"  Average: {stats['avg_lock_wait'] * 1000:.2f}ms")
            print(f"  Median (P50): {p50 * 1000:.2f}ms")
            print(f"  P95: {p95 * 1000:.2f}ms")
            print(f"  P99: {p99 * 1000:.2f}ms")
            print(f"  Max: {stats['max_lock_wait'] * 1000:.2f}ms")
    
    def test_lock_contention_vs_throughput(
        self,
        concurrent_models,
        concurrent_test_data,
        transaction_context
    ):
        """
        测试锁竞争程度与吞吐量的关系。
        
        验证点：
        1. 不同并发度下的吞吐量
        2. 锁竞争对性能的影响
        3. 最优并发度
        """
        Account, Counter, LockTest = concurrent_models
        
        # 固定数量的热点账户
        num_accounts = 10
        accounts = [Account(name=f"acc_{i}", balance=1000.0) for i in range(num_accounts)]
        for acc in accounts:
            acc.save()
        
        thread_counts = [5, 10, 20, 50]
        results = []
        
        for num_threads in thread_counts:
            metrics = ConcurrentMetrics()
            updates_per_thread = 50
            
            def worker():
                import random
                for _ in range(updates_per_thread):
                    account_idx = random.randint(0, num_accounts - 1)
                    try:
                        with transaction_context:
                            acc = Account.find(accounts[account_idx].id)
                            acc.balance += 1.0
                            acc.save()
                        metrics.record_success()
                    except:
                        metrics.record_failure()
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker) for _ in range(num_threads)]
                for future in as_completed(futures):
                    future.result()
            
            elapsed = time.time() - start_time
            metrics.total_time = elapsed
            
            stats = metrics.get_stats()
            
            results.append({
                'threads': num_threads,
                'throughput': stats['throughput'],
                'avg_wait': stats['avg_lock_wait'] * 1000
            })
            
            print(f"Threads: {num_threads}, "
                  f"Throughput: {stats['throughput']:.0f} ops/s, "
                  f"Avg wait: {stats['avg_lock_wait'] * 1000:.2f}ms")
        
        # 找到最优并发度
        best = max(results, key=lambda x: x['throughput'])
        print(f"\nOptimal concurrency: {best['threads']} threads "
              f"({best['throughput']:.0f} ops/s)")
```

---

## 5. 性能基准目标

### 5.1 只读并发
- **线性扩展**: 吞吐量应随线程数近似线性增长（效率 > 80%）
- **无锁等待**: 平均锁等待时间 < 1ms

### 5.2 写写冲突
- **锁等待时间**: 平均 < 10ms
- **死锁率**: < 1%（在合理的并发负载下）
- **吞吐量**: 支持 50-100 TPS（取决于硬件）

### 5.3 隔离级别影响
- **READ COMMITTED**: 基准性能
- **REPEATABLE READ**: 吞吐量下降 10-20%
- **SERIALIZABLE**: 吞吐量下降 30-50%

---

## 6. 测试数据规模

### 6.1 Small Scale
- 线程数: 5-10
- 账户数: 50-100
- 操作数: 100-500

### 6.2 Medium Scale
- 线程数: 10-20
- 账户数: 200-500
- 操作数: 1000-5000

### 6.3 Large Scale
- 线程数: 50-100
- 账户数: 1000-5000
- 操作数: 10000+

---

## 7. 所需能力

```python
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    TransactionCapability,
    LockingCapability
)

required_capabilities = [
    (CapabilityCategory.TRANSACTION, TransactionCapability.BASIC_TRANSACTION),
    (CapabilityCategory.LOCKING, LockingCapability.ROW_LEVEL_LOCKING)
]

optional_capabilities = [
    (CapabilityCategory.TRANSACTION, TransactionCapability.ISOLATION_LEVELS),
    (CapabilityCategory.LOCKING, LockingCapability.DEADLOCK_DETECTION)
]
```

---

## 8. 实施注意事项

### 8.1 测试环境
- 使用多核CPU
- 控制其他负载
- 网络延迟最小化

### 8.2 结果解读
- 并发性能高度依赖硬件
- 不同数据库表现差异大
- 隔离级别选择权衡一致性和性能

### 8.3 优化建议
- 减少事务持有时间
- 避免长事务
- 合理设置并发度
- 使用乐观锁（适当场景）
- 按顺序获取锁（避免死锁）

---

本实施方案提供了并发事务基准测试的完整框架。