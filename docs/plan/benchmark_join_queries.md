# 基准测试 - 联接查询性能测试实施方案

## 测试目标

测量和比较不同类型联接查询的性能特征，包括两表联接、多表联接、不同联接类型和不同数据基数的联接性能。

## Provider 接口定义

### IJoinQueryBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class IJoinQueryBenchmarkProvider(ABC):
    """联接查询基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_join_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # Table1
        Type[ActiveRecord],  # Table2
        Type[ActiveRecord],  # Table3
        Type[ActiveRecord],  # Table4
        Type[ActiveRecord]   # Table5
    ]:
        """设置联接测试模型（5个表）"""
        pass
    
    @abstractmethod
    def populate_join_data(
        self,
        table1_count: int,
        cardinality: str  # "1:1", "1:N", "N:M"
    ):
        """预填充联接测试数据"""
        pass
    
    @abstractmethod
    def create_indexes(self, table_name: str, columns: List[str]):
        """创建索引"""
        pass
    
    @abstractmethod
    def cleanup_benchmark_data(self, scenario: str):
        """清理基准测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def join_models(request):
    """联接测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_join_query_benchmark_provider()
    
    models = provider.setup_join_models(scenario)
    yield models
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def join_data_1to1(request, join_models):
    """一对一关系数据"""
    provider = get_join_query_benchmark_provider()
    provider.populate_join_data(table1_count=10000, cardinality="1:1")
    return "1:1"

@pytest.fixture
def join_data_1toN(request, join_models):
    """一对多关系数据"""
    provider = get_join_query_benchmark_provider()
    provider.populate_join_data(table1_count=10000, cardinality="1:N")
    return "1:N"

@pytest.fixture
def join_data_NtoM(request, join_models):
    """多对多关系数据"""
    provider = get_join_query_benchmark_provider()
    provider.populate_join_data(table1_count=10000, cardinality="N:M")
    return "N:M"

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestTwoTableJoin - 两表联接测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestTwoTableJoin:
    """两表联接性能测试"""
    
    def test_inner_join_1to1(self, join_models, join_data_1to1, benchmark_metrics):
        """测试INNER JOIN（一对一）"""
        pass
    
    def test_inner_join_1toN(self, join_models, join_data_1toN, benchmark_metrics):
        """测试INNER JOIN（一对多）"""
        pass
    
    def test_left_join_1to1(self, join_models, join_data_1to1, benchmark_metrics):
        """测试LEFT JOIN（一对一）"""
        pass
    
    def test_left_join_1toN(self, join_models, join_data_1toN, benchmark_metrics):
        """测试LEFT JOIN（一对多）"""
        pass
    
    def test_right_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试RIGHT JOIN"""
        pass
    
    def test_join_with_where(self, join_models, join_data_1toN, benchmark_metrics):
        """测试带WHERE条件的JOIN"""
        pass
```

### TestThreeTableJoin - 三表联接测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestThreeTableJoin:
    """三表联接性能测试"""
    
    def test_three_table_inner_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试三表INNER JOIN"""
        pass
    
    def test_three_table_left_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试三表LEFT JOIN"""
        pass
    
    def test_three_table_mixed_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试三表混合JOIN"""
        pass
    
    def test_join_order_impact(self, join_models, join_data_1toN, benchmark_metrics):
        """测试JOIN顺序影响"""
        pass
```

### TestFiveTableJoin - 五表联接测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
@pytest.mark.slow
class TestFiveTableJoin:
    """五表联接性能测试"""
    
    def test_five_table_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试五表JOIN"""
        pass
    
    def test_star_schema_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试星型模式JOIN"""
        pass
    
    def test_chain_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试链式JOIN"""
        pass
```

### TestSelfJoin - 自联接测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestSelfJoin:
    """自联接性能测试"""
    
    def test_simple_self_join(self, join_models, benchmark_metrics):
        """测试简单自联接"""
        pass
    
    def test_hierarchical_self_join(self, join_models, benchmark_metrics):
        """测试层次结构自联接"""
        pass
    
    def test_self_join_depth_impact(self, join_models, benchmark_metrics):
        """测试自联接深度影响"""
        pass
```

### TestJoinCardinality - 联接基数测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestJoinCardinality:
    """联接基数影响测试"""
    
    def test_one_to_one_join(self, join_models, join_data_1to1, benchmark_metrics):
        """测试一对一联接"""
        pass
    
    def test_one_to_few_join(self, join_models, benchmark_metrics):
        """测试一对少（平均2-5条）联接"""
        pass
    
    def test_one_to_many_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试一对多（平均10-100条）联接"""
        pass
    
    def test_many_to_many_join(self, join_models, join_data_NtoM, benchmark_metrics):
        """测试多对多联接"""
        pass
    
    def test_cardinality_impact(self, join_models, benchmark_metrics):
        """测试基数对性能的影响"""
        pass
```

### TestJoinWithIndexes - 带索引联接测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestJoinWithIndexes:
    """带索引的联接测试"""
    
    def test_join_with_fk_index(self, join_models, join_data_1toN, benchmark_metrics):
        """测试外键索引联接"""
        pass
    
    def test_join_without_index(self, join_models, benchmark_metrics):
        """测试无索引联接"""
        pass
    
    def test_index_impact_on_join(self, join_models, benchmark_metrics):
        """测试索引对JOIN的影响"""
        pass
    
    def test_composite_index_join(self, join_models, benchmark_metrics):
        """测试复合索引联接"""
        pass
```

### TestJoinResultSetSize - 联接结果集大小测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestJoinResultSetSize:
    """联接结果集大小影响测试"""
    
    @pytest.mark.small_scale
    def test_small_result_set(self, join_models, benchmark_metrics):
        """测试小结果集（<100条）"""
        pass
    
    @pytest.mark.medium_scale
    def test_medium_result_set(self, join_models, benchmark_metrics):
        """测试中等结果集（100-1000条）"""
        pass
    
    @pytest.mark.large_scale
    def test_large_result_set(self, join_models, join_data_1toN, benchmark_metrics):
        """测试大结果集（>1000条）"""
        pass
    
    def test_result_set_scalability(self, join_models, benchmark_metrics):
        """测试结果集可扩展性"""
        pass
```

### TestJoinTypes - 联接类型对比测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestJoinTypes:
    """联接类型性能对比"""
    
    def test_inner_vs_left_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试INNER vs LEFT JOIN"""
        pass
    
    def test_left_vs_right_join(self, join_models, join_data_1toN, benchmark_metrics):
        """测试LEFT vs RIGHT JOIN"""
        pass
    
    def test_cross_join_performance(self, join_models, benchmark_metrics):
        """测试CROSS JOIN性能"""
        pass
```

### TestJoinOptimization - 联接优化测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestJoinOptimization:
    """联接优化测试"""
    
    def test_join_with_subquery(self, join_models, join_data_1toN, benchmark_metrics):
        """测试带子查询的JOIN"""
        pass
    
    def test_join_buffer_size_impact(self, join_models, benchmark_metrics):
        """测试JOIN缓冲区大小影响"""
        pass
    
    def test_join_algorithm_comparison(self, join_models, benchmark_metrics):
        """测试JOIN算法对比（Nested Loop, Hash, Merge）"""
        pass
```

### TestJoinMemoryUsage - 联接内存使用测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.memory_intensive
class TestJoinMemoryUsage:
    """联接内存使用测试"""
    
    def test_two_table_join_memory(self, join_models, join_data_1toN, benchmark_metrics):
        """测试两表JOIN内存使用"""
        pass
    
    def test_five_table_join_memory(self, join_models, join_data_1toN, benchmark_metrics):
        """测试五表JOIN内存使用"""
        pass
    
    def test_memory_vs_result_set_size(self, join_models, benchmark_metrics):
        """测试内存使用与结果集大小关系"""
        pass
```

### TestJoinQueryPlan - 联接查询计划测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestJoinQueryPlan:
    """联接查询计划验证"""
    
    def test_verify_join_algorithm(self, join_models, join_data_1toN):
        """测试验证JOIN算法"""
        pass
    
    def test_verify_index_usage_in_join(self, join_models):
        """测试验证JOIN中的索引使用"""
        pass
    
    def test_join_cost_estimation(self, join_models, join_data_1toN):
        """测试JOIN成本估算"""
        pass
```

## 性能基准和预期

### 性能指标

1. **两表联接**
   - 一对一：10-50ms（10K行）
   - 一对多：50-200ms（10K行，平均10条关联）
   - 带索引 vs 无索引：5-10倍性能差异

2. **多表联接**
   - 三表联接：100-300ms
   - 五表联接：200-1000ms
   - 每增加一个表：约50-100%性能下降

3. **联接基数**
   - 一对一：最快
   - 一对多：与关联数线性增长
   - 多对多：最慢，笛卡尔积影响

4. **结果集大小**
   - 小结果集（<100）：50-100ms
   - 中等结果集（100-1000）：100-500ms
   - 大结果集（>1000）：>500ms

### 优化建议

1. **索引策略**
   - 外键列必须有索引
   - JOIN条件列建立索引
   - 复合索引用于多条件JOIN

2. **JOIN优化**
   - 优先过滤小表
   - 避免不必要的JOIN
   - 使用EXPLAIN分析执行计划
   - 考虑JOIN顺序

3. **数据建模**
   - 避免过度规范化
   - 考虑反规范化高频JOIN
   - 合理设计外键关系

### 所需能力（Capabilities）

- **INNER JOIN**：`JoinCapability.INNER_JOIN`
- **LEFT JOIN**：`JoinCapability.LEFT_JOIN`
- **RIGHT JOIN**：`JoinCapability.RIGHT_JOIN`
- **外键支持**：`ForeignKeyCapability.FOREIGN_KEY`

### 测试数据特征

- **表大小**：每表1K-100K记录
- **关系基数**：
  - 一对一：1:1
  - 一对多：1:10-100
  - 多对多：N:M（通过中间表）
- **索引配置**：外键列有索引

### 报告格式

基准测试结果应包含：
- 查询响应时间（平均、P95、P99）
- JOIN类型对比
- 表数量影响曲线
- 基数影响分析
- 索引使用情况
- 查询计划分析
- 内存使用情况
