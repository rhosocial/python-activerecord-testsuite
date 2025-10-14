# 基准测试 - 批量插入性能测试实施方案

## 测试目标

测量和比较不同规模、不同配置下批量插入操作的性能特征，包括插入速度、内存使用、数据库增长等关键指标。

## Provider 接口定义

### IBulkInsertBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, List, Dict, Tuple
from rhosocial.activerecord import ActiveRecord

class IBulkInsertBenchmarkProvider(ABC):
    """批量插入基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_benchmark_model(self, scenario: str) -> Type[ActiveRecord]:
        """设置基准测试模型"""
        pass
    
    @abstractmethod
    def generate_test_data(
        self,
        count: int,
        field_count: int = 10
    ) -> List[Dict]:
        """生成测试数据"""
        pass
    
    @abstractmethod
    def setup_with_indexes(self, scenario: str) -> Type[ActiveRecord]:
        """设置带索引的模型"""
        pass
    
    @abstractmethod
    def setup_with_foreign_keys(self, scenario: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
        """设置带外键的模型"""
        pass
    
    @abstractmethod
    def get_database_size(self) -> int:
        """获取数据库大小（字节）"""
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
    provider = get_bulk_benchmark_provider()
    
    model = provider.setup_benchmark_model(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def benchmark_model_with_indexes(request):
    """带索引的基准测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_bulk_benchmark_provider()
    
    model = provider.setup_with_indexes(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def benchmark_models_with_fk(request):
    """带外键的基准测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_bulk_benchmark_provider()
    
    models = provider.setup_with_foreign_keys(scenario)
    yield models
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def test_data_1k(request):
    """1K测试数据"""
    provider = get_bulk_benchmark_provider()
    return provider.generate_test_data(count=1000)

@pytest.fixture
def test_data_10k(request):
    """10K测试数据"""
    provider = get_bulk_benchmark_provider()
    return provider.generate_test_data(count=10000)

@pytest.fixture
def test_data_100k(request):
    """100K测试数据"""
    provider = get_bulk_benchmark_provider()
    return provider.generate_test_data(count=100000)

@pytest.fixture
def test_data_1m(request):
    """1M测试数据"""
    provider = get_bulk_benchmark_provider()
    return provider.generate_test_data(count=1000000)

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestSingleInsertBaseline - 单条插入基准测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.small_scale
class TestSingleInsertBaseline:
    """单条插入基准测试（作为对比基准）"""
    
    def test_single_insert_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试单条插入1K记录"""
        pass
    
    def test_single_insert_10k(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试单条插入10K记录"""
        pass
```

### TestBatchInsert - 批量插入测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestBatchInsert:
    """批量插入性能测试"""
    
    @pytest.mark.small_scale
    def test_batch_insert_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试批量插入1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_batch_insert_10k(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试批量插入10K记录"""
        pass
    
    @pytest.mark.large_scale
    def test_batch_insert_100k(self, benchmark_model, test_data_100k, benchmark_metrics):
        """测试批量插入100K记录"""
        pass
    
    @pytest.mark.large_scale
    @pytest.mark.slow
    def test_batch_insert_1m(self, benchmark_model, test_data_1m, benchmark_metrics):
        """测试批量插入1M记录"""
        pass
```

### TestBatchSizeOptimization - 批量大小优化测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestBatchSizeOptimization:
    """批量大小优化测试"""
    
    def test_batch_size_100(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试批量大小100"""
        pass
    
    def test_batch_size_500(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试批量大小500"""
        pass
    
    def test_batch_size_1000(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试批量大小1000"""
        pass
    
    def test_batch_size_5000(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试批量大小5000"""
        pass
    
    def test_optimal_batch_size(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试确定最优批量大小"""
        pass
```

### TestInsertWithIndexes - 带索引插入测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestInsertWithIndexes:
    """带索引的批量插入测试"""
    
    @pytest.mark.small_scale
    def test_insert_no_index_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试无索引插入1K记录"""
        pass
    
    @pytest.mark.small_scale
    def test_insert_with_index_1k(self, benchmark_model_with_indexes, test_data_1k, benchmark_metrics):
        """测试带索引插入1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_insert_no_index_10k(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试无索引插入10K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_insert_with_index_10k(self, benchmark_model_with_indexes, test_data_10k, benchmark_metrics):
        """测试带索引插入10K记录"""
        pass
    
    def test_index_overhead(self, benchmark_model, benchmark_model_with_indexes, test_data_10k):
        """测试索引开销"""
        pass
```

### TestInsertWithForeignKeys - 带外键插入测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestInsertWithForeignKeys:
    """带外键的批量插入测试"""
    
    def test_insert_with_fk_validation(self, benchmark_models_with_fk, benchmark_metrics):
        """测试带外键验证的插入"""
        pass
    
    def test_insert_without_fk_validation(self, benchmark_models_with_fk, benchmark_metrics):
        """测试禁用外键验证的插入"""
        pass
    
    def test_fk_validation_overhead(self, benchmark_models_with_fk):
        """测试外键验证开销"""
        pass
```

### TestTransactionalInsert - 事务性插入测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestTransactionalInsert:
    """事务性批量插入测试"""
    
    @pytest.mark.small_scale
    def test_insert_with_transaction_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试事务内插入1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_insert_with_transaction_10k(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试事务内插入10K记录"""
        pass
    
    @pytest.mark.small_scale
    def test_insert_without_transaction_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试非事务插入1K记录"""
        pass
    
    def test_transaction_overhead(self, benchmark_model, test_data_10k):
        """测试事务开销"""
        pass
```

### TestMemoryUsage - 内存使用测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.memory_intensive
class TestMemoryUsage:
    """批量插入内存使用测试"""
    
    @pytest.mark.small_scale
    def test_memory_usage_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试1K记录插入的内存使用"""
        pass
    
    @pytest.mark.medium_scale
    def test_memory_usage_10k(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试10K记录插入的内存使用"""
        pass
    
    @pytest.mark.large_scale
    def test_memory_usage_100k(self, benchmark_model, test_data_100k, benchmark_metrics):
        """测试100K记录插入的内存使用"""
        pass
    
    def test_memory_per_record(self, benchmark_model, benchmark_metrics):
        """测试每条记录的平均内存使用"""
        pass
    
    def test_peak_memory(self, benchmark_model, test_data_100k, benchmark_metrics):
        """测试峰值内存使用"""
        pass
```

### TestDatabaseGrowth - 数据库增长测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestDatabaseGrowth:
    """数据库大小增长测试"""
    
    def test_db_size_growth_1k(self, benchmark_model, test_data_1k):
        """测试插入1K记录的数据库增长"""
        pass
    
    def test_db_size_growth_10k(self, benchmark_model, test_data_10k):
        """测试插入10K记录的数据库增长"""
        pass
    
    def test_size_per_record(self, benchmark_model, test_data_10k):
        """测试每条记录的平均存储大小"""
        pass
```

### TestThroughput - 吞吐量测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestThroughput:
    """批量插入吞吐量测试"""
    
    def test_records_per_second_1k(self, benchmark_model, test_data_1k, benchmark_metrics):
        """测试1K规模的插入速率"""
        pass
    
    def test_records_per_second_10k(self, benchmark_model, test_data_10k, benchmark_metrics):
        """测试10K规模的插入速率"""
        pass
    
    def test_records_per_second_100k(self, benchmark_model, test_data_100k, benchmark_metrics):
        """测试100K规模的插入速率"""
        pass
    
    def test_throughput_scalability(self, benchmark_model, benchmark_metrics):
        """测试吞吐量可扩展性"""
        pass
```

## 性能基准和预期

### 性能指标

1. **插入速率**
   - 单条插入：100-1,000 条/秒
   - 批量插入（无索引）：10,000-100,000 条/秒
   - 批量插入（带索引）：5,000-50,000 条/秒

2. **内存使用**
   - 每条记录：100-500 字节（内存）
   - 峰值内存：< 数据量 * 2

3. **数据库增长**
   - 每条记录：200-1,000 字节（磁盘）
   - 索引开销：20-50% 额外空间

4. **事务开销**
   - 事务包装开销：< 10% 总时间

### 优化目标

1. **批量大小优化**
   - 找到最优批量大小（通常 500-5000）
   - 平衡内存使用和插入速度

2. **索引策略**
   - 量化索引对插入性能的影响
   - 建议延迟索引创建策略

3. **事务配置**
   - 确定事务批量的最佳实践
   - 平衡一致性和性能

### 所需能力（Capabilities）

- **批量插入**：`BulkOperationCapability.BULK_INSERT`
- **多行插入**：`BulkOperationCapability.MULTI_ROW_INSERT`
- **事务支持**：`TransactionCapability.BASIC`

### 测试数据特征

- **记录大小**：10-20 个字段，总大小 200-500 字节
- **数据类型**：混合（整数、字符串、日期、浮点数）
- **数据分布**：随机生成，模拟真实场景

### 报告格式

基准测试结果应包含：
- 操作总时间
- 记录数/秒（吞吐量）
- 峰值内存使用
- 平均内存/记录
- 数据库大小增长
- 与基准的对比（单条插入）
