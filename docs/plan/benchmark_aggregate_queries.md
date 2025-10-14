# 基准测试 - 聚合查询性能测试实施方案

## 测试目标

测量和比较不同类型聚合查询的性能特征，包括基本聚合函数、GROUP BY、HAVING子句、多聚合函数和聚合联接查询的性能。

## Provider 接口定义

### IAggregateQueryBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple
from rhosocial.activerecord import ActiveRecord

class IAggregateQueryBenchmarkProvider(ABC):
    """聚合查询基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_aggregate_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # SalesData
        Type[ActiveRecord],  # OrderData
        Type[ActiveRecord]   # CustomerData
    ]:
        """设置聚合测试模型"""
        pass
    
    @abstractmethod
    def populate_aggregate_data(
        self,
        record_count: int,
        group_cardinality: int  # GROUP BY后的组数
    ):
        """预填充聚合测试数据"""
        pass
    
    @abstractmethod
    def cleanup_benchmark_data(self, scenario: str):
        """清理基准测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def aggregate_models(request):
    """聚合测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_aggregate_query_benchmark_provider()
    
    models = provider.setup_aggregate_models(scenario)
    yield models
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def aggregate_data_low_cardinality(request, aggregate_models):
    """低基数数据（10组）"""
    provider = get_aggregate_query_benchmark_provider()
    provider.populate_aggregate_data(record_count=100000, group_cardinality=10)
    return (100000, 10)

@pytest.fixture
def aggregate_data_medium_cardinality(request, aggregate_models):
    """中等基数数据（1000组）"""
    provider = get_aggregate_query_benchmark_provider()
    provider.populate_aggregate_data(record_count=100000, group_cardinality=1000)
    return (100000, 1000)

@pytest.fixture
def aggregate_data_high_cardinality(request, aggregate_models):
    """高基数数据（10000组）"""
    provider = get_aggregate_query_benchmark_provider()
    provider.populate_aggregate_data(record_count=100000, group_cardinality=10000)
    return (100000, 10000)

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestBasicAggregates - 基本聚合测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestBasicAggregates:
    """基本聚合函数性能测试"""
    
    def test_count_all(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试COUNT(*)"""
        pass
    
    def test_count_distinct(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试COUNT(DISTINCT)"""
        pass
    
    def test_sum_function(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试SUM()"""
        pass
    
    def test_avg_function(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试AVG()"""
        pass
    
    def test_min_function(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试MIN()"""
        pass
    
    def test_max_function(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试MAX()"""
        pass
```

### TestGroupBy - GROUP BY测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestGroupBy:
    """GROUP BY性能测试"""
    
    @pytest.mark.small_scale
    def test_group_by_low_cardinality(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试低基数GROUP BY（10组）"""
        pass
    
    @pytest.mark.medium_scale
    def test_group_by_medium_cardinality(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试中等基数GROUP BY（1000组）"""
        pass
    
    @pytest.mark.large_scale
    def test_group_by_high_cardinality(self, aggregate_models, aggregate_data_high_cardinality, benchmark_metrics):
        """测试高基数GROUP BY（10000组）"""
        pass
    
    def test_group_by_multiple_columns(self, aggregate_models, benchmark_metrics):
        """测试多列GROUP BY"""
        pass
    
    def test_group_by_with_index(self, aggregate_models, benchmark_metrics):
        """测试带索引的GROUP BY"""
        pass
    
    def test_cardinality_impact(self, aggregate_models, benchmark_metrics):
        """测试基数对GROUP BY性能的影响"""
        pass
```

### TestHavingClause - HAVING子句测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestHavingClause:
    """HAVING子句性能测试"""
    
    def test_having_simple_condition(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试简单HAVING条件"""
        pass
    
    def test_having_complex_condition(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试复杂HAVING条件"""
        pass
    
    def test_having_vs_where(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试HAVING vs WHERE性能对比"""
        pass
    
    def test_having_with_aggregate(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试HAVING中使用聚合函数"""
        pass
```

### TestMultipleAggregates - 多聚合函数测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestMultipleAggregates:
    """多聚合函数性能测试"""
    
    def test_single_aggregate(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试单个聚合函数（基准）"""
        pass
    
    def test_two_aggregates(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试两个聚合函数"""
        pass
    
    def test_five_aggregates(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试五个聚合函数"""
        pass
    
    def test_ten_aggregates(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试十个聚合函数"""
        pass
    
    def test_aggregate_count_impact(self, aggregate_models, benchmark_metrics):
        """测试聚合函数数量对性能的影响"""
        pass
```

### TestAggregateWithJoin - 聚合联接测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestAggregateWithJoin:
    """聚合与JOIN组合性能测试"""
    
    def test_aggregate_after_join(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试JOIN后聚合"""
        pass
    
    def test_join_with_grouped_data(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试联接已分组数据"""
        pass
    
    def test_multiple_table_aggregate(self, aggregate_models, benchmark_metrics):
        """测试多表聚合"""
        pass
    
    def test_aggregate_join_order(self, aggregate_models, benchmark_metrics):
        """测试聚合和JOIN的执行顺序影响"""
        pass
```

### TestDistinctCount - DISTINCT计数测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestDistinctCount:
    """DISTINCT计数性能测试"""
    
    @pytest.mark.small_scale
    def test_distinct_low_cardinality(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试低基数DISTINCT"""
        pass
    
    @pytest.mark.medium_scale
    def test_distinct_medium_cardinality(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试中等基数DISTINCT"""
        pass
    
    @pytest.mark.large_scale
    def test_distinct_high_cardinality(self, aggregate_models, aggregate_data_high_cardinality, benchmark_metrics):
        """测试高基数DISTINCT"""
        pass
    
    def test_count_vs_count_distinct(self, aggregate_models, benchmark_metrics):
        """测试COUNT vs COUNT DISTINCT性能对比"""
        pass
```

### TestOrderByWithAggregate - 聚合排序测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestOrderByWithAggregate:
    """聚合结果排序性能测试"""
    
    def test_order_by_aggregate_result(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试按聚合结果排序"""
        pass
    
    def test_order_by_group_column(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试按分组列排序"""
        pass
    
    def test_order_by_multiple_aggregates(self, aggregate_models, benchmark_metrics):
        """测试按多个聚合结果排序"""
        pass
```

### TestLimitWithAggregate - 聚合限制测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestLimitWithAggregate:
    """聚合结果限制性能测试"""
    
    def test_top_n_groups(self, aggregate_models, aggregate_data_high_cardinality, benchmark_metrics):
        """测试TOP N分组"""
        pass
    
    def test_limit_impact_on_aggregate(self, aggregate_models, aggregate_data_high_cardinality, benchmark_metrics):
        """测试LIMIT对聚合性能的影响"""
        pass
    
    def test_pagination_of_aggregated_results(self, aggregate_models, aggregate_data_high_cardinality, benchmark_metrics):
        """测试聚合结果分页"""
        pass
```

### TestAggregateIndexUsage - 聚合索引使用测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestAggregateIndexUsage:
    """聚合查询索引使用测试"""
    
    def test_aggregate_with_index(self, aggregate_models, aggregate_data_medium_cardinality, benchmark_metrics):
        """测试带索引的聚合"""
        pass
    
    def test_aggregate_without_index(self, aggregate_models, benchmark_metrics):
        """测试无索引的聚合"""
        pass
    
    def test_covering_index_for_aggregate(self, aggregate_models, benchmark_metrics):
        """测试覆盖索引聚合"""
        pass
    
    def test_index_impact_on_group_by(self, aggregate_models, benchmark_metrics):
        """测试索引对GROUP BY的影响"""
        pass
```

### TestAggregateMemoryUsage - 聚合内存使用测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.memory_intensive
class TestAggregateMemoryUsage:
    """聚合查询内存使用测试"""
    
    def test_low_cardinality_memory(self, aggregate_models, aggregate_data_low_cardinality, benchmark_metrics):
        """测试低基数聚合内存"""
        pass
    
    def test_high_cardinality_memory(self, aggregate_models, aggregate_data_high_cardinality, benchmark_metrics):
        """测试高基数聚合内存"""
        pass
    
    def test_memory_vs_group_count(self, aggregate_models, benchmark_metrics):
        """测试内存使用与分组数关系"""
        pass
```

### TestAggregateQueryPlan - 聚合查询计划测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestAggregateQueryPlan:
    """聚合查询计划验证"""
    
    def test_verify_aggregate_algorithm(self, aggregate_models, aggregate_data_medium_cardinality):
        """测试验证聚合算法"""
        pass
    
    def test_verify_sort_for_group_by(self, aggregate_models):
        """测试验证GROUP BY排序"""
        pass
    
    def test_aggregate_cost_estimation(self, aggregate_models, aggregate_data_medium_cardinality):
        """测试聚合成本估算"""
        pass
```

## 性能基准和预期

### 性能指标

1. **基本聚合**
   - COUNT(*)：50-200ms（100K行）
   - COUNT(DISTINCT)：100-500ms（基数相关）
   - SUM/AVG/MIN/MAX：50-200ms

2. **GROUP BY**
   - 低基数（10组）：100-300ms
   - 中等基数（1000组）：200-800ms
   - 高基数（10000组）：500-2000ms
   - 性能与分组数近似线性关系

3. **多聚合函数**
   - 单个聚合：基准
   - 5个聚合：10-20% 性能下降
   - 10个聚合：20-40% 性能下降

4. **聚合联接**
   - 聚合后JOIN：快于JOIN后聚合
   - 性能下降：50-200%（相比单表聚合）

5. **DISTINCT计数**
   - 低基数：快于高基数
   - 高基数：接近全表扫描性能

### 优化建议

1. **GROUP BY优化**
   - 在GROUP BY列上创建索引
   - 降低分组基数
   - 使用覆盖索引

2. **聚合优化**
   - 先过滤再聚合
   - 避免不必要的DISTINCT
   - 使用物化视图存储聚合结果

3. **联接聚合**
   - 先聚合小表再联接
   - 避免在大结果集上聚合

### 所需能力（Capabilities）

- **COUNT**：`AggregateFunctionCapability.COUNT`
- **SUM**：`AggregateFunctionCapability.SUM`
- **AVG**：`AggregateFunctionCapability.AVG`
- **MIN/MAX**：`AggregateFunctionCapability.MIN_MAX`
- **GROUP BY**：`QueryCapability.GROUP_BY`
- **HAVING**：`QueryCapability.HAVING`
- **DISTINCT**：`QueryCapability.DISTINCT`

### 测试数据特征

- **记录数**：10K-1M记录
- **分组基数**：10-10000组
- **数据分布**：均匀分布和倾斜分布
- **聚合列类型**：整数、浮点数、日期

### 报告格式

基准测试结果应包含：
- 查询响应时间（平均、P95、P99）
- 基数影响曲线
- 聚合函数数量影响
- 索引使用情况
- 内存使用情况
- 查询计划分析
- 优化建议
