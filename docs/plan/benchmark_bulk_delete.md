# 基准测试 - 批量删除性能测试实施方案

## 测试目标

测量和比较不同规模、不同配置下批量删除操作的性能特征，包括删除速度、级联删除开销、空间回收等关键指标。

## Provider 接口定义

### IBulkDeleteBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, List, Dict, Tuple
from rhosocial.activerecord import ActiveRecord

class IBulkDeleteBenchmarkProvider(ABC):
    """批量删除基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_benchmark_model(self, scenario: str) -> Type[ActiveRecord]:
        """设置基准测试模型"""
        pass
    
    @abstractmethod
    def setup_with_foreign_keys(self, scenario: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
        """设置带外键的模型（用于级联测试）"""
        pass
    
    @abstractmethod
    def populate_test_data(
        self,
        count: int,
        field_count: int = 10
    ):
        """预填充测试数据"""
        pass
    
    @abstractmethod
    def populate_with_relations(
        self,
        parent_count: int,
        children_per_parent: int
    ):
        """预填充带关系的数据"""
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
    provider = get_bulk_delete_benchmark_provider()
    
    model = provider.setup_benchmark_model(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def benchmark_models_with_fk(request):
    """带外键的基准测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_bulk_delete_benchmark_provider()
    
    models = provider.setup_with_foreign_keys(scenario)
    yield models
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def populated_data_1k(request, benchmark_model):
    """1K预填充数据"""
    provider = get_bulk_delete_benchmark_provider()
    provider.populate_test_data(count=1000)
    return 1000

@pytest.fixture
def populated_data_10k(request, benchmark_model):
    """10K预填充数据"""
    provider = get_bulk_delete_benchmark_provider()
    provider.populate_test_data(count=10000)
    return 10000

@pytest.fixture
def populated_data_100k(request, benchmark_model):
    """100K预填充数据"""
    provider = get_bulk_delete_benchmark_provider()
    provider.populate_test_data(count=100000)
    return 100000

@pytest.fixture
def populated_with_relations(request, benchmark_models_with_fk):
    """带关系的预填充数据"""
    provider = get_bulk_delete_benchmark_provider()
    provider.populate_with_relations(parent_count=1000, children_per_parent=10)
    return (1000, 10)

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestSingleDeleteBaseline - 单条删除基准测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.small_scale
class TestSingleDeleteBaseline:
    """单条删除基准测试（作为对比基准）"""
    
    def test_single_delete_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试单条删除1K记录"""
        pass
    
    def test_single_delete_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试单条删除10K记录"""
        pass
```

### TestBatchDelete - 批量删除测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestBatchDelete:
    """批量删除性能测试"""
    
    @pytest.mark.small_scale
    def test_batch_delete_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试批量删除1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_batch_delete_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试批量删除10K记录"""
        pass
    
    @pytest.mark.large_scale
    def test_batch_delete_100k(self, benchmark_model, populated_data_100k, benchmark_metrics):
        """测试批量删除100K记录"""
        pass
```

### TestConditionalDelete - 条件删除测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestConditionalDelete:
    """条件删除性能测试"""
    
    def test_delete_with_simple_condition(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试简单条件删除"""
        pass
    
    def test_delete_with_complex_condition(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试复杂条件删除"""
        pass
    
    def test_delete_with_range_condition(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试范围条件删除"""
        pass
    
    def test_delete_by_ids(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试按ID列表删除"""
        pass
```

### TestTruncateTable - 表截断测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestTruncateTable:
    """表截断性能测试"""
    
    @pytest.mark.small_scale
    def test_truncate_vs_delete_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试截断 vs 删除 (1K)"""
        pass
    
    @pytest.mark.medium_scale
    def test_truncate_vs_delete_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试截断 vs 删除 (10K)"""
        pass
    
    @pytest.mark.large_scale
    def test_truncate_vs_delete_100k(self, benchmark_model, populated_data_100k, benchmark_metrics):
        """测试截断 vs 删除 (100K)"""
        pass
    
    def test_truncate_speed_advantage(self, benchmark_model, benchmark_metrics):
        """测试截断的速度优势"""
        pass
```

### TestCascadeDelete - 级联删除测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestCascadeDelete:
    """级联删除性能测试"""
    
    def test_delete_with_cascade(self, benchmark_models_with_fk, populated_with_relations, benchmark_metrics):
        """测试级联删除"""
        pass
    
    def test_cascade_one_to_many(self, benchmark_models_with_fk, populated_with_relations, benchmark_metrics):
        """测试一对多级联删除"""
        pass
    
    def test_cascade_depth_impact(self, benchmark_models_with_fk, benchmark_metrics):
        """测试级联深度影响"""
        pass
    
    def test_cascade_vs_manual_delete(self, benchmark_models_with_fk, populated_with_relations, benchmark_metrics):
        """测试级联删除 vs 手动删除"""
        pass
    
    def test_foreign_key_check_overhead(self, benchmark_models_with_fk, populated_with_relations):
        """测试外键检查开销"""
        pass
```

### TestSoftDelete - 软删除测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestSoftDelete:
    """软删除性能测试"""
    
    def test_soft_delete_vs_hard_delete(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试软删除 vs 硬删除"""
        pass
    
    def test_soft_delete_performance(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试软删除性能"""
        pass
    
    def test_query_with_soft_deleted(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试查询时排除软删除记录"""
        pass
```

### TestDeleteThroughput - 删除吞吐量测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestDeleteThroughput:
    """批量删除吞吐量测试"""
    
    def test_deletes_per_second_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试1K规模的删除速率"""
        pass
    
    def test_deletes_per_second_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试10K规模的删除速率"""
        pass
    
    def test_deletes_per_second_100k(self, benchmark_model, populated_data_100k, benchmark_metrics):
        """测试100K规模的删除速率"""
        pass
    
    def test_throughput_scalability(self, benchmark_model, benchmark_metrics):
        """测试吞吐量可扩展性"""
        pass
```

### TestSpaceReclamation - 空间回收测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.large_scale
class TestSpaceReclamation:
    """空间回收测试"""
    
    def test_database_size_before_delete(self, benchmark_model, populated_data_100k):
        """测试删除前数据库大小"""
        pass
    
    def test_database_size_after_delete(self, benchmark_model, populated_data_100k):
        """测试删除后数据库大小"""
        pass
    
    def test_space_reclamation_immediate(self, benchmark_model, populated_data_100k):
        """测试立即空间回收"""
        pass
    
    def test_vacuum_performance(self, benchmark_model, populated_data_100k, benchmark_metrics):
        """测试VACUUM操作性能"""
        pass
    
    def test_fragmentation_impact(self, benchmark_model):
        """测试碎片化影响"""
        pass
```

### TestDeleteWithIndexes - 带索引删除测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestDeleteWithIndexes:
    """带索引的删除测试"""
    
    def test_delete_indexed_table(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试有索引表的删除"""
        pass
    
    def test_delete_non_indexed_table(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试无索引表的删除"""
        pass
    
    def test_index_maintenance_overhead(self, benchmark_model, populated_data_10k):
        """测试索引维护开销"""
        pass
    
    def test_multiple_indexes_impact(self, benchmark_model, populated_data_10k):
        """测试多索引影响"""
        pass
```

### TestTransactionalDelete - 事务性删除测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
class TestTransactionalDelete:
    """事务性批量删除测试"""
    
    @pytest.mark.small_scale
    def test_delete_with_transaction_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试事务内删除1K记录"""
        pass
    
    @pytest.mark.medium_scale
    def test_delete_with_transaction_10k(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试事务内删除10K记录"""
        pass
    
    @pytest.mark.small_scale
    def test_delete_without_transaction_1k(self, benchmark_model, populated_data_1k, benchmark_metrics):
        """测试非事务删除1K记录"""
        pass
    
    def test_transaction_overhead(self, benchmark_model, populated_data_10k):
        """测试事务开销"""
        pass
    
    def test_rollback_performance(self, benchmark_model, populated_data_10k, benchmark_metrics):
        """测试回滚性能"""
        pass
```

### TestBatchSizeOptimization - 批量大小优化测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.medium_scale
class TestBatchSizeOptimization:
    """批量删除大小优化测试"""
    
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

### TestDeleteVerification - 删除验证测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_bulk
@pytest.mark.small_scale
class TestDeleteVerification:
    """批量删除正确性验证"""
    
    def test_delete_accuracy(self, benchmark_model, populated_data_1k):
        """测试删除准确性"""
        pass
    
    def test_partial_delete_handling(self, benchmark_model, populated_data_1k):
        """测试部分删除处理"""
        pass
    
    def test_cascade_integrity(self, benchmark_models_with_fk, populated_with_relations):
        """测试级联删除完整性"""
        pass
```

## 性能基准和预期

### 性能指标

1. **删除速率**
   - 单条删除：100-500 条/秒
   - 批量删除（无外键）：10,000-100,000 条/秒
   - 批量删除（有外键）：5,000-50,000 条/秒
   - 表截断：< 1秒（任意大小）

2. **级联删除**
   - 一对多级联：50-80% 性能下降
   - 深度级联：每层 20-30% 额外开销

3. **索引影响**
   - 索引维护开销：10-30% 性能下降
   - 多索引累积影响：每个额外索引 5-10% 下降

4. **空间回收**
   - 立即回收：部分数据库支持
   - VACUUM操作：1-10分钟（100K记录）

5. **软删除**
   - 软删除速度：接近更新操作速度
   - 比硬删除快 80-95%

### 优化目标

1. **批量大小优化**
   - 找到最优批量大小（通常 1000-10000）
   - 平衡事务大小和性能

2. **级联策略**
   - 量化级联删除开销
   - 建议手动删除 vs 级联删除的使用场景

3. **空间管理**
   - 定期VACUUM策略
   - 碎片化监控和处理

4. **截断使用**
   - 识别可以使用TRUNCATE的场景
   - 截断 vs 删除的决策指南

### 所需能力（Capabilities）

- **批量删除**：`BulkOperationCapability.BATCH_DELETE`
- **截断表**：`DDLCapability.TRUNCATE_TABLE`
- **级联删除**：`ForeignKeyCapability.CASCADE_DELETE`
- **事务支持**：`TransactionCapability.BASIC`

### 测试数据特征

- **记录大小**：10-20 个字段，总大小 200-500 字节
- **数据类型**：混合（整数、字符串、日期、浮点数）
- **关系深度**：1-3层级联关系

### 报告格式

基准测试结果应包含：
- 操作总时间
- 记录数/秒（吞吐量）
- 与基准的对比（单条删除、截断）
- 级联删除开销
- 空间回收情况
- 最优批量大小建议
- 截断 vs 删除的性能对比
