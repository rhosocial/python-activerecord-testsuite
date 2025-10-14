# 基准测试 - 批量更新性能测试实施方案

## 测试目标

测量和比较不同规模、不同配置下批量更新操作的性能特征，包括更新速度、锁定开销、索引影响等关键指标。

## Provider 接口定义

### IBulkUpdateBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, List, Dict, Tuple
from rhosocial.activerecord import ActiveRecord

class IBulkUpdateBenchmarkProvider(ABC):
    """批量更新基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_benchmark_model(self, scenario: str) -> Type[ActiveRecord]:
        """设置基准测试模型"""
        pass
    
    @abstractmethod
    def setup_with_indexes(self, scenario: str) -> Type[ActiveRecord]:
        """设置带索引的模型"""
        pass
    
    @abstractmethod
    def populate_test_data(
        self,
        count: int,
        field_count: int = 10
    ) -> List[Dict]:
        """预填充测试数据"""
        pass
    
    @abstractmethod
    def generate_update_data(
        self,
        count: int,
        fields_to_update: int
    ) -> List[Dict]:
        """生成更新数据"""
        pass
    
    @abstractmethod
    def cleanup_benchmark_data(self, scenario: str):
        """清理基准测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def benchmark_model(request):
    """基准测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_bulk_update_benchmark_provider()
    
    model = provider.setup_benchmark_model(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def benchmark_model_with_indexes(request):
    """带索引的基准测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_bulk_update_benchmark_provider()
    
    model = provider.setup_with_indexes(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def populated_data_1k(request, benchmark_model):
    """1K预填充数据"""
    provider = get_bulk_update_benchmark_provider()
    provider.populate_test_data(count=1000)
    return 1000

@pytest.fixture
def populated_data_10k(request, benchmark_model):
    """10K预填充数据"""
    provider = get_bulk_update_benchmark_provider()
    provider.populate_test_data(count=10000)
    return 10000

@pytest.fixture
def populated_data_100k(request, benchmark_model):
    """100K预填充数据"""
    provider = get_bulk_update_benchmark_provider()
    provider.populate_test_data(count=100000)
    return 100000

@pytest.fixture
def update_data_1k(request):
    """1K更新数据"""
    provider = get_bulk_update_benchmark_provider()
    return provider.generate_update_data(count=1000, fields_to_update=3)

@pytest.fixture
def update_data_10k(request):
    """10K更新数据"""
    provider = get_bulk_update_benchmark_provider()
    return provider.generate_update_data(count=10000, fields_to_update=3)

@pytest.fixture
def update_data_100k(request):
    """100K更新数据"""
    provider = get_bulk_update_benchmark_provider()
    return provider.generate_update_data(count=100000, fields_to_update=3)

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestSingleUpdateBaseline - 单条更新基准测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.small_scale
class TestSingleUpdateBaseline:
    """单条更新基准测试（作为对比基准）"""
    
    def test_single_update_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试单条更新1K记录"""
        pass
    
    def test_single_update_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试单条更新10K记录"""
        pass
```

### TestBatchUpdate - 批量更新测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestBatchUpdate:
    """批量更新性能测试"""
    
    @pytest.mark.small_scale
    def test_batch_update_1k(self, benchmark_model, populated_data_1k, update_data_1k, benchmark_metrics):
        """测试批量更新1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_batch_update_10k(self, benchmark_model, populated_data_10k, update_data_10k, benchmark_metrics):
        """测试批量更新10K记录"""
        pass
    
    @pytest.mark.large_scale
    def test_batch_update_100k(self, benchmark_model, populated_data_100k, update_data_100k, benchmark_metrics):
        """测试批量更新100K记录"""
        pass
```

### TestConditionalUpdate - 条件更新测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestConditionalUpdate:
    """条件更新性能测试"""
    
    def test_update_with_simple_condition(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试简单条件更新"""
        pass
    
    def test_update_with_complex_condition(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试复杂条件更新"""
        pass
    
    def test_update_with_range_condition(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试范围条件更新"""
        pass
    
    def test_update_subset_vs_full_table(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试部分更新 vs 全表更新"""
        pass
```

### TestMultiFieldUpdate - 多字段更新测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestMultiFieldUpdate:
    """多字段更新性能测试"""
    
    def test_update_single_field(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试更新单个字段"""
        pass
    
    def test_update_three_fields(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试更新3个字段"""
        pass
    
    def test_update_five_fields(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试更新5个字段"""
        pass
    
    def test_update_ten_fields(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试更新10个字段"""
        pass
    
    def test_field_count_impact(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试字段数量对性能的影响"""
        pass
```

### TestUpdateWithIndexes - 带索引更新测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestUpdateWithIndexes:
    """带索引的批量更新测试"""
    
    @pytest.mark.small_scale
    def test_update_no_index_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试无索引更新1K记录"""
        pass
    
    @pytest.mark.small_scale
    def test_update_with_index_1k(self, benchmark_model_with_indexes, populated_data_1k, benchmark_metrics):
        """测试带索引更新1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_update_no_index_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试无索引更新10K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_update_with_index_10k(self, benchmark_model_with_indexes, populated_data_10k, benchmark_metrics):
        """测试带索引更新10K记录"""
        pass
    
    def test_index_overhead(self, benchmark_model, benchmark_model_with_indexes, populated_data_10k):
        """测试索引开销"""
        pass
    
    def test_update_indexed_vs_nonindexed_field(self, benchmark_model_with_indexes, populated_data_10k):
        """测试更新索引字段 vs 非索引字段"""
        pass
```

### TestTransactionalUpdate - 事务性更新测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestTransactionalUpdate:
    """事务性批量更新测试"""
    
    @pytest.mark.small_scale
    def test_update_with_transaction_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试事务内更新1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_update_with_transaction_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试事务内更新10K记录"""
        pass
    
    @pytest.mark.small_scale
    def test_update_without_transaction_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试非事务更新1K记录"""
        pass
    
    def test_transaction_overhead(self, benchmark_model, populated_data_10k):
        """测试事务开销"""
        pass
```

### TestConcurrentUpdates - 并发更新测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestConcurrentUpdates:
    """并发更新性能测试"""
    
    def test_sequential_updates(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试顺序更新（基准）"""
        pass
    
    def test_concurrent_updates_different_rows(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试并发更新不同行"""
        pass
    
    def test_concurrent_updates_same_rows(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试并发更新相同行（锁竞争）"""
        pass
    
    def test_lock_contention(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试锁竞争开销"""
        pass
    
    def test_optimal_concurrency_level(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试最优并发级别"""
        pass
```

### TestBatchSizeOptimization - 批量大小优化测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestBatchSizeOptimization:
    """批量更新大小优化测试"""
    
    def test_batch_size_100(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试批量大小100"""
        pass
    
    def test_batch_size_500(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试批量大小500"""
        pass
    
    def test_batch_size_1000(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试批量大小1000"""
        pass
    
    def test_batch_size_5000(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试批量大小5000"""
        pass
    
    def test_optimal_batch_size(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试确定最优批量大小"""
        pass
```

### TestUpdateThroughput - 更新吞吐量测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestUpdateThroughput:
    """批量更新吞吐量测试"""
    
    def test_updates_per_second_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试1K规模的更新速率"""
        pass
    
    def test_updates_per_second_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试10K规模的更新速率"""
        pass
    
    def test_updates_per_second_100k(self, benchmark_model, populated_data_100k, benchmark_metrics):
        """测试100K规模的更新速率"""
        pass
    
    def test_throughput_scalability(self, benchmark_model, benchmark_metrics):
        """测试吞吐量可扩展性"""
        pass
```

### TestUpdateVerification - 更新验证测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.small_scale
class TestUpdateVerification:
    """批量更新正确性验证"""
    
    def test_update_accuracy(self, benchmark_model, populated_data_1k):
        """测试更新准确性"""
        pass
    
    def test_partial_update_handling(self, benchmark_model, populated_data_1k):
        """测试部分更新处理"""
        pass
    
    def test_update_rollback(self, benchmark_model, populated_data_1k):
        """测试更新回滚"""
        pass
```

## 性能基准和预期

### 性能指标

1. **更新速率**
   - 单条更新：100-500 条/秒
   - 批量更新（无索引）：5,000-50,000 条/秒
   - 批量更新（带索引）：2,000-20,000 条/秒

2. **索引影响**
   - 索引开销：30-60% 性能下降
   - 多索引累积影响：每个额外索引 10-20% 下降

3. **字段数量影响**
   - 单字段更新：基准性能
   - 3字段更新：5-10% 下降
   - 10字段更新：20-30% 下降

4. **事务开销**
   - 事务包装开销：< 15% 总时间

5. **并发性能**
   - 无锁竞争：接近线性扩展
   - 有锁竞争：显著性能下降

### 优化目标

1. **批量大小优化**
   - 找到最优批量大小（通常 500-5000）
   - 平衡内存使用和更新速度

2. **索引策略**
   - 量化索引对更新性能的影响
   - 建议索引使用最佳实践

3. **并发配置**
   - 确定最优并发级别
   - 避免过度锁竞争

### 所需能力（Capabilities）

- **批量更新**：`BulkOperationCapability.BATCH_UPDATE`
- **条件更新**：`QueryCapability.WHERE_CLAUSE`
- **事务支持**：`TransactionCapability.BASIC`

### 测试数据特征

- **记录大小**：10-20 个字段，总大小 200-500 字节
- **数据类型**：混合（整数、字符串、日期、浮点数）
- **更新模式**：部分字段更新（1-10个字段）

### 报告格式

基准测试结果应包含：
- 操作总时间
- 记录数/秒（吞吐量）
- 与基准的对比（单条更新）
- 索引影响百分比
- 最优批量大小建议
- 并发性能曲线
