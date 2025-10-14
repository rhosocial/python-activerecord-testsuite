# 基准测试 - 复杂查询性能测试实施方案

## 测试目标

测量和比较复杂查询的性能特征，包括子查询、CTE、递归CTE、窗口函数、UNION查询和嵌套查询的性能。

## Provider 接口定义

### IComplexQueryBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class IComplexQueryBenchmarkProvider(ABC):
    """复杂查询基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_complex_query_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # OrderData
        Type[ActiveRecord],  # CustomerData
        Type[ActiveRecord],  # ProductData
        Type[ActiveRecord],  # CategoryData (层次结构)
        Type[ActiveRecord]   # TreeNode (递归测试)
    ]:
        """设置复杂查询测试模型"""
        pass
    
    @abstractmethod
    def populate_hierarchical_data(
        self,
        root_count: int,
        max_depth: int,
        children_per_node: int
    ):
        """预填充层次结构数据"""
        pass
    
    @abstractmethod
    def populate_relational_data(
        self,
        customer_count: int,
        orders_per_customer: int
    ):
        """预填充关系数据"""
        pass
    
    @abstractmethod
    def cleanup_benchmark_data(self, scenario: str):
        """清理基准测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def complex_query_models(request):
    """复杂查询测试模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_complex_query_benchmark_provider()
    
    models = provider.setup_complex_query_models(scenario)
    yield models
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def hierarchical_data_shallow(request, complex_query_models):
    """浅层次数据（深度3）"""
    provider = get_complex_query_benchmark_provider()
    provider.populate_hierarchical_data(root_count=10, max_depth=3, children_per_node=5)
    return (10, 3, 5)

@pytest.fixture
def hierarchical_data_deep(request, complex_query_models):
    """深层次数据（深度10）"""
    provider = get_complex_query_benchmark_provider()
    provider.populate_hierarchical_data(root_count=5, max_depth=10, children_per_node=3)
    return (5, 10, 3)

@pytest.fixture
def relational_data(request, complex_query_models):
    """关系数据"""
    provider = get_complex_query_benchmark_provider()
    provider.populate_relational_data(customer_count=1000, orders_per_customer=10)
    return (1000, 10)

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestSubqueries - 子查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestSubqueries:
    """子查询性能测试"""
    
    def test_scalar_subquery(self, complex_query_models, relational_data, benchmark_metrics):
        """测试标量子查询"""
        pass
    
    def test_correlated_subquery(self, complex_query_models, relational_data, benchmark_metrics):
        """测试相关子查询"""
        pass
    
    def test_non_correlated_subquery(self, complex_query_models, relational_data, benchmark_metrics):
        """测试非相关子查询"""
        pass
    
    def test_in_subquery(self, complex_query_models, relational_data, benchmark_metrics):
        """测试IN子查询"""
        pass
    
    def test_exists_subquery(self, complex_query_models, relational_data, benchmark_metrics):
        """测试EXISTS子查询"""
        pass
    
    def test_correlated_vs_join(self, complex_query_models, relational_data, benchmark_metrics):
        """测试相关子查询 vs JOIN性能对比"""
        pass
```

### TestCTEQueries - CTE查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
@requires_capabilities((CapabilityCategory.CTE, CTECapability.BASIC_CTE))
class TestCTEQueries:
    """CTE（公共表表达式）性能测试"""
    
    def test_simple_cte(self, complex_query_models, relational_data, benchmark_metrics):
        """测试简单CTE"""
        pass
    
    def test_multiple_ctes(self, complex_query_models, relational_data, benchmark_metrics):
        """测试多个CTE"""
        pass
    
    def test_nested_ctes(self, complex_query_models, relational_data, benchmark_metrics):
        """测试嵌套CTE"""
        pass
    
    def test_cte_with_join(self, complex_query_models, relational_data, benchmark_metrics):
        """测试CTE与JOIN组合"""
        pass
    
    def test_cte_vs_subquery(self, complex_query_models, relational_data, benchmark_metrics):
        """测试CTE vs 子查询性能对比"""
        pass
```

### TestRecursiveCTE - 递归CTE测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@requires_capabilities((CapabilityCategory.CTE, CTECapability.RECURSIVE_CTE))
class TestRecursiveCTE:
    """递归CTE性能测试"""
    
    @pytest.mark.small_scale
    def test_recursive_cte_shallow(self, complex_query_models, hierarchical_data_shallow, benchmark_metrics):
        """测试浅递归CTE（深度3）"""
        pass
    
    @pytest.mark.medium_scale
    def test_recursive_cte_deep(self, complex_query_models, hierarchical_data_deep, benchmark_metrics):
        """测试深递归CTE（深度10）"""
        pass
    
    def test_recursive_depth_impact(self, complex_query_models, benchmark_metrics):
        """测试递归深度对性能的影响"""
        pass
    
    def test_recursive_breadth_impact(self, complex_query_models, benchmark_metrics):
        """测试递归广度对性能的影响"""
        pass
    
    def test_recursive_termination(self, complex_query_models, hierarchical_data_deep, benchmark_metrics):
        """测试递归终止条件"""
        pass
    
    def test_hierarchical_query(self, complex_query_models, hierarchical_data_deep, benchmark_metrics):
        """测试层次结构查询"""
        pass
```

### TestWindowFunctions - 窗口函数测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
@requires_capabilities((CapabilityCategory.WINDOW_FUNCTIONS, WindowFunctionCapability.ROW_NUMBER))
class TestWindowFunctions:
    """窗口函数性能测试"""
    
    def test_row_number(self, complex_query_models, relational_data, benchmark_metrics):
        """测试ROW_NUMBER()"""
        pass
    
    def test_rank_function(self, complex_query_models, relational_data, benchmark_metrics):
        """测试RANK()"""
        pass
    
    def test_dense_rank(self, complex_query_models, relational_data, benchmark_metrics):
        """测试DENSE_RANK()"""
        pass
    
    def test_lag_lead(self, complex_query_models, relational_data, benchmark_metrics):
        """测试LAG/LEAD"""
        pass
    
    def test_partition_by(self, complex_query_models, relational_data, benchmark_metrics):
        """测试PARTITION BY性能"""
        pass
    
    def test_window_with_order_by(self, complex_query_models, relational_data, benchmark_metrics):
        """测试带ORDER BY的窗口函数"""
        pass
    
    def test_multiple_window_functions(self, complex_query_models, relational_data, benchmark_metrics):
        """测试多个窗口函数"""
        pass
```

### TestUnionQueries - UNION查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestUnionQueries:
    """UNION查询性能测试"""
    
    def test_union_two_tables(self, complex_query_models, benchmark_metrics):
        """测试两表UNION"""
        pass
    
    def test_union_all_vs_union(self, complex_query_models, benchmark_metrics):
        """测试UNION ALL vs UNION"""
        pass
    
    def test_union_multiple_tables(self, complex_query_models, benchmark_metrics):
        """测试多表UNION"""
        pass
    
    def test_union_with_order_by(self, complex_query_models, benchmark_metrics):
        """测试UNION带ORDER BY"""
        pass
    
    def test_union_result_set_size(self, complex_query_models, benchmark_metrics):
        """测试UNION结果集大小影响"""
        pass
```

### TestIntersectExcept - INTERSECT/EXCEPT测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
@requires_capabilities((CapabilityCategory.SET_OPERATIONS, SetOperationCapability.INTERSECT))
class TestIntersectExcept:
    """INTERSECT/EXCEPT性能测试"""
    
    def test_intersect_query(self, complex_query_models, benchmark_metrics):
        """测试INTERSECT查询"""
        pass
    
    def test_except_query(self, complex_query_models, benchmark_metrics):
        """测试EXCEPT查询"""
        pass
    
    def test_intersect_vs_join(self, complex_query_models, benchmark_metrics):
        """测试INTERSECT vs JOIN性能对比"""
        pass
```

### TestNestedQueries - 嵌套查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestNestedQueries:
    """嵌套查询性能测试"""
    
    def test_two_level_nesting(self, complex_query_models, relational_data, benchmark_metrics):
        """测试两层嵌套"""
        pass
    
    def test_three_level_nesting(self, complex_query_models, relational_data, benchmark_metrics):
        """测试三层嵌套"""
        pass
    
    def test_five_level_nesting(self, complex_query_models, relational_data, benchmark_metrics):
        """测试五层嵌套"""
        pass
    
    def test_nesting_depth_impact(self, complex_query_models, benchmark_metrics):
        """测试嵌套深度对性能的影响"""
        pass
```

### TestDerivedTables - 派生表测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestDerivedTables:
    """派生表性能测试"""
    
    def test_simple_derived_table(self, complex_query_models, relational_data, benchmark_metrics):
        """测试简单派生表"""
        pass
    
    def test_derived_table_with_aggregate(self, complex_query_models, relational_data, benchmark_metrics):
        """测试带聚合的派生表"""
        pass
    
    def test_join_derived_tables(self, complex_query_models, relational_data, benchmark_metrics):
        """测试联接派生表"""
        pass
    
    def test_nested_derived_tables(self, complex_query_models, relational_data, benchmark_metrics):
        """测试嵌套派生表"""
        pass
```

### TestComplexJoinPatterns - 复杂联接模式测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestComplexJoinPatterns:
    """复杂联接模式性能测试"""
    
    def test_lateral_join(self, complex_query_models, relational_data, benchmark_metrics):
        """测试LATERAL JOIN"""
        pass
    
    def test_cross_apply(self, complex_query_models, relational_data, benchmark_metrics):
        """测试CROSS APPLY"""
        pass
    
    def test_outer_apply(self, complex_query_models, relational_data, benchmark_metrics):
        """测试OUTER APPLY"""
        pass
```

### TestQueryOptimization - 查询优化测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestQueryOptimization:
    """查询优化性能测试"""
    
    def test_query_rewrite_impact(self, complex_query_models, relational_data, benchmark_metrics):
        """测试查询重写影响"""
        pass
    
    def test_predicate_pushdown(self, complex_query_models, relational_data, benchmark_metrics):
        """测试谓词下推"""
        pass
    
    def test_join_elimination(self, complex_query_models, relational_data, benchmark_metrics):
        """测试JOIN消除"""
        pass
    
    def test_materialization_strategy(self, complex_query_models, benchmark_metrics):
        """测试物化策略"""
        pass
```

### TestComplexQueryMemory - 复杂查询内存测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.memory_intensive
class TestComplexQueryMemory:
    """复杂查询内存使用测试"""
    
    def test_recursive_cte_memory(self, complex_query_models, hierarchical_data_deep, benchmark_metrics):
        """测试递归CTE内存"""
        pass
    
    def test_window_function_memory(self, complex_query_models, relational_data, benchmark_metrics):
        """测试窗口函数内存"""
        pass
    
    def test_nested_query_memory(self, complex_query_models, relational_data, benchmark_metrics):
        """测试嵌套查询内存"""
        pass
    
    def test_memory_vs_complexity(self, complex_query_models, benchmark_metrics):
        """测试内存使用与查询复杂度关系"""
        pass
```

### TestQueryPlanComplexity - 查询计划复杂度测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestQueryPlanComplexity:
    """查询计划复杂度验证"""
    
    def test_simple_vs_complex_plan(self, complex_query_models):
        """测试简单 vs 复杂查询计划"""
        pass
    
    def test_plan_optimization_time(self, complex_query_models, benchmark_metrics):
        """测试查询计划优化时间"""
        pass
    
    def test_execution_plan_verification(self, complex_query_models):
        """测试执行计划验证"""
        pass
```

## 性能基准和预期

### 性能指标

1. **子查询**
   - 非相关子查询：50-200ms
   - 相关子查询：200-1000ms（慢于JOIN）
   - EXISTS vs IN：相似性能

2. **CTE**
   - 简单CTE：与子查询相似
   - 多个CTE：线性增长
   - 可读性好，性能可接受

3. **递归CTE**
   - 浅递归（深度3）：100-300ms
   - 深递归（深度10）：500-2000ms
   - 性能与深度和广度相关

4. **窗口函数**
   - ROW_NUMBER：100-500ms
   - RANK/DENSE_RANK：类似性能
   - LAG/LEAD：稍慢
   - 与结果集大小线性关系

5. **UNION**
   - UNION ALL：快于UNION（无需去重）
   - 多表UNION：线性增长

### 优化建议

1. **子查询优化**
   - 优先使用JOIN替代相关子查询
   - 使用EXISTS替代IN（大数据集）
   - 考虑CTE提高可读性

2. **递归查询**
   - 限制递归深度
   - 添加终止条件
   - 考虑使用闭包表

3. **窗口函数**
   - 减少PARTITION BY基数
   - 合并多个窗口函数
   - 考虑物化中间结果

4. **复杂查询通用**
   - 简化查询逻辑
   - 使用EXPLAIN分析
   - 考虑物化视图
   - 适当的索引策略

### 所需能力（Capabilities）

- **基本CTE**：`CTECapability.BASIC_CTE`
- **递归CTE**：`CTECapability.RECURSIVE_CTE`
- **窗口函数**：`WindowFunctionCapability.*`
- **集合操作**：`SetOperationCapability.*`
- **子查询**：`QueryCapability.SUBQUERY`

### 测试数据特征

- **层次数据**：3-10层深度
- **关系数据**：1000客户，10000订单
- **数据分布**：均匀和倾斜分布
- **结果集**：100-10000行

### 报告格式

基准测试结果应包含：
- 查询响应时间（平均、P95、P99）
- 查询类型性能对比
- 复杂度影响分析
- 内存使用情况
- 查询计划分析
- 优化建议
- 替代方案性能对比
