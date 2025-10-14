# 基准测试 - 简单查询性能测试实施方案

## 测试目标

测量和比较不同类型简单查询的性能特征，包括主键查询、索引查询、全表扫描、LIKE查询和IN查询等的响应时间和吞吐量。

## Provider 接口定义

### ISimpleQueryBenchmarkProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, List, Dict
from rhosocial.activerecord import ActiveRecord

class ISimpleQueryBenchmarkProvider(ABC):
    """简单查询基准测试数据提供者接口"""
    
    @abstractmethod
    def setup_query_model(self, scenario: str) -> Type[ActiveRecord]:
        """设置查询测试模型（带主键和索引）"""
        pass
    
    @abstractmethod
    def setup_model_without_indexes(self, scenario: str) -> Type[ActiveRecord]:
        """设置无索引模型（用于全表扫描测试）"""
        pass
    
    @abstractmethod
    def populate_test_data(
        self,
        count: int,
        with_indexes: bool = True
    ):
        """预填充测试数据"""
        pass
    
    @abstractmethod
    def get_random_ids(self, count: int) -> List[int]:
        """获取随机ID列表"""
        pass
    
    @abstractmethod
    def get_random_indexed_values(self, count: int) -> List[str]:
        """获取随机索引列值"""
        pass
    
    @abstractmethod
    def cleanup_benchmark_data(self, scenario: str):
        """清理基准测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def query_model(request):
    """带索引的查询模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_simple_query_benchmark_provider()
    
    model = provider.setup_query_model(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def query_model_no_index(request):
    """无索引的查询模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_simple_query_benchmark_provider()
    
    model = provider.setup_model_without_indexes(scenario)
    yield model
    
    provider.cleanup_benchmark_data(scenario)

@pytest.fixture
def populated_data_1k(request, query_model):
    """1K数据"""
    provider = get_simple_query_benchmark_provider()
    provider.populate_test_data(count=1000, with_indexes=True)
    return 1000

@pytest.fixture
def populated_data_10k(request, query_model):
    """10K数据"""
    provider = get_simple_query_benchmark_provider()
    provider.populate_test_data(count=10000, with_indexes=True)
    return 10000

@pytest.fixture
def populated_data_100k(request, query_model):
    """100K数据"""
    provider = get_simple_query_benchmark_provider()
    provider.populate_test_data(count=100000, with_indexes=True)
    return 100000

@pytest.fixture
def populated_data_1m(request, query_model):
    """1M数据"""
    provider = get_simple_query_benchmark_provider()
    provider.populate_test_data(count=1000000, with_indexes=True)
    return 1000000

@pytest.fixture
def benchmark_metrics():
    """基准测试指标收集器"""
    from rhosocial.activerecord.testsuite.benchmark.utils import BenchmarkMetrics
    return BenchmarkMetrics()
```

## 测试类和函数签名

### TestPrimaryKeyLookup - 主键查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestPrimaryKeyLookup:
    """主键查询性能测试"""
    
    @pytest.mark.small_scale
    def test_pk_lookup_1k_dataset(self, query_model, populated_data_1k, benchmark_metrics):
        """测试主键查询（1K数据集）"""
        pass
    
    @pytest.mark.medium_scale
    def test_pk_lookup_10k_dataset(self, query_model, populated_data_10k, benchmark_metrics):
        """测试主键查询（10K数据集）"""
        pass
    
    @pytest.mark.large_scale
    def test_pk_lookup_100k_dataset(self, query_model, populated_data_100k, benchmark_metrics):
        """测试主键查询（100K数据集）"""
        pass
    
    @pytest.mark.large_scale
    def test_pk_lookup_1m_dataset(self, query_model, populated_data_1m, benchmark_metrics):
        """测试主键查询（1M数据集）"""
        pass
    
    def test_pk_lookup_consistency(self, query_model, populated_data_100k, benchmark_metrics):
        """测试主键查询一致性（多次查询）"""
        pass
    
    def test_sequential_vs_random_pk_lookup(self, query_model, populated_data_100k, benchmark_metrics):
        """测试顺序 vs 随机主键查询"""
        pass
```

### TestIndexedColumnSearch - 索引列搜索测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestIndexedColumnSearch:
    """索引列搜索性能测试"""
    
    @pytest.mark.small_scale
    def test_indexed_search_1k(self, query_model, populated_data_1k, benchmark_metrics):
        """测试索引列搜索（1K）"""
        pass
    
    @pytest.mark.medium_scale
    def test_indexed_search_10k(self, query_model, populated_data_10k, benchmark_metrics):
        """测试索引列搜索（10K）"""
        pass
    
    @pytest.mark.large_scale
    def test_indexed_search_100k(self, query_model, populated_data_100k, benchmark_metrics):
        """测试索引列搜索（100K）"""
        pass
    
    def test_indexed_equality_search(self, query_model, populated_data_100k, benchmark_metrics):
        """测试等值搜索（索引）"""
        pass
    
    def test_indexed_range_search(self, query_model, populated_data_100k, benchmark_metrics):
        """测试范围搜索（索引）"""
        pass
    
    def test_index_selectivity_impact(self, query_model, populated_data_100k, benchmark_metrics):
        """测试索引选择性影响"""
        pass
```

### TestNonIndexedSearch - 非索引搜索测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestNonIndexedSearch:
    """非索引列搜索性能测试"""
    
    @pytest.mark.small_scale
    def test_full_scan_1k(self, query_model_no_index, benchmark_metrics):
        """测试全表扫描（1K）"""
        pass
    
    @pytest.mark.medium_scale
    def test_full_scan_10k(self, query_model_no_index, benchmark_metrics):
        """测试全表扫描（10K）"""
        pass
    
    @pytest.mark.large_scale
    def test_full_scan_100k(self, query_model_no_index, benchmark_metrics):
        """测试全表扫描（100K）"""
        pass
    
    def test_indexed_vs_non_indexed(self, query_model, query_model_no_index, benchmark_metrics):
        """测试索引 vs 非索引查询对比"""
        pass
    
    def test_table_scan_scalability(self, query_model_no_index, benchmark_metrics):
        """测试全表扫描可扩展性"""
        pass
```

### TestLikeQueries - LIKE查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestLikeQueries:
    """LIKE查询性能测试"""
    
    def test_like_prefix_match(self, query_model, populated_data_10k, benchmark_metrics):
        """测试前缀匹配（LIKE 'abc%'）"""
        pass
    
    def test_like_suffix_match(self, query_model, populated_data_10k, benchmark_metrics):
        """测试后缀匹配（LIKE '%xyz'）"""
        pass
    
    def test_like_contains_match(self, query_model, populated_data_10k, benchmark_metrics):
        """测试包含匹配（LIKE '%abc%'）"""
        pass
    
    def test_like_with_index(self, query_model, populated_data_10k, benchmark_metrics):
        """测试带索引的LIKE查询"""
        pass
    
    def test_like_without_index(self, query_model_no_index, benchmark_metrics):
        """测试无索引的LIKE查询"""
        pass
    
    def test_case_sensitive_vs_insensitive(self, query_model, populated_data_10k, benchmark_metrics):
        """测试大小写敏感 vs 不敏感"""
        pass
```

### TestInQueries - IN查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestInQueries:
    """IN查询性能测试"""
    
    def test_in_query_small_list(self, query_model, populated_data_10k, benchmark_metrics):
        """测试IN查询（10个值）"""
        pass
    
    def test_in_query_medium_list(self, query_model, populated_data_10k, benchmark_metrics):
        """测试IN查询（100个值）"""
        pass
    
    def test_in_query_large_list(self, query_model, populated_data_10k, benchmark_metrics):
        """测试IN查询（1000个值）"""
        pass
    
    def test_in_query_scalability(self, query_model, populated_data_10k, benchmark_metrics):
        """测试IN查询可扩展性"""
        pass
    
    def test_in_vs_multiple_or(self, query_model, populated_data_10k, benchmark_metrics):
        """测试IN vs 多个OR"""
        pass
    
    def test_in_with_index(self, query_model, populated_data_10k, benchmark_metrics):
        """测试带索引的IN查询"""
        pass
```

### TestRangeQueries - 范围查询测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestRangeQueries:
    """范围查询性能测试"""
    
    def test_range_narrow(self, query_model, populated_data_100k, benchmark_metrics):
        """测试窄范围查询（结果集<1%）"""
        pass
    
    def test_range_medium(self, query_model, populated_data_100k, benchmark_metrics):
        """测试中等范围查询（结果集1-10%）"""
        pass
    
    def test_range_wide(self, query_model, populated_data_100k, benchmark_metrics):
        """测试宽范围查询（结果集>10%）"""
        pass
    
    def test_between_query(self, query_model, populated_data_100k, benchmark_metrics):
        """测试BETWEEN查询"""
        pass
    
    def test_range_with_index(self, query_model, populated_data_100k, benchmark_metrics):
        """测试带索引的范围查询"""
        pass
    
    def test_range_result_set_impact(self, query_model, populated_data_100k, benchmark_metrics):
        """测试结果集大小对性能的影响"""
        pass
```

### TestComparisonOperators - 比较运算符测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestComparisonOperators:
    """比较运算符性能测试"""
    
    def test_equality_operator(self, query_model, populated_data_100k, benchmark_metrics):
        """测试等于运算符（=）"""
        pass
    
    def test_inequality_operator(self, query_model, populated_data_100k, benchmark_metrics):
        """测试不等于运算符（!=）"""
        pass
    
    def test_greater_than(self, query_model, populated_data_100k, benchmark_metrics):
        """测试大于运算符（>）"""
        pass
    
    def test_less_than(self, query_model, populated_data_100k, benchmark_metrics):
        """测试小于运算符（<）"""
        pass
    
    def test_operator_performance_comparison(self, query_model, populated_data_100k):
        """测试运算符性能对比"""
        pass
```

### TestResultSetSize - 结果集大小测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
class TestResultSetSize:
    """结果集大小影响测试"""
    
    @pytest.mark.small_scale
    def test_single_result(self, query_model, populated_data_100k, benchmark_metrics):
        """测试单个结果"""
        pass
    
    @pytest.mark.small_scale
    def test_small_result_set(self, query_model, populated_data_100k, benchmark_metrics):
        """测试小结果集（10-100条）"""
        pass
    
    @pytest.mark.medium_scale
    def test_medium_result_set(self, query_model, populated_data_100k, benchmark_metrics):
        """测试中等结果集（100-1000条）"""
        pass
    
    @pytest.mark.large_scale
    def test_large_result_set(self, query_model, populated_data_100k, benchmark_metrics):
        """测试大结果集（1000+条）"""
        pass
    
    def test_result_set_scalability(self, query_model, populated_data_100k, benchmark_metrics):
        """测试结果集可扩展性"""
        pass
```

### TestQueryCaching - 查询缓存测试

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestQueryCaching:
    """查询缓存性能测试"""
    
    def test_first_query(self, query_model, populated_data_100k, benchmark_metrics):
        """测试首次查询（冷缓存）"""
        pass
    
    def test_repeated_query(self, query_model, populated_data_100k, benchmark_metrics):
        """测试重复查询（热缓存）"""
        pass
    
    def test_cache_hit_rate(self, query_model, populated_data_100k, benchmark_metrics):
        """测试缓存命中率"""
        pass
    
    def test_cache_vs_no_cache(self, query_model, populated_data_100k):
        """测试缓存 vs 无缓存对比"""
        pass
```

### TestQueryPlanVerification - 查询计划验证

```python
@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.medium_scale
class TestQueryPlanVerification:
    """查询计划验证测试"""
    
    def test_verify_index_usage(self, query_model, populated_data_100k):
        """测试验证索引使用"""
        pass
    
    def test_verify_table_scan(self, query_model_no_index):
        """测试验证全表扫描"""
        pass
    
    def test_query_cost_estimation(self, query_model, populated_data_100k):
        """测试查询成本估算"""
        pass
```

## 性能基准和预期

### 性能指标

1. **主键查询**
   - 响应时间：< 1ms（任意数据规模）
   - O(1)复杂度（哈希索引）或 O(log n)（B-tree索引）

2. **索引查询**
   - 等值查询：< 10ms（100K数据）
   - 范围查询：10-50ms（结果集大小相关）

3. **全表扫描**
   - 1K记录：10-50ms
   - 10K记录：50-200ms
   - 100K记录：200-1000ms
   - 线性增长 O(n)

4. **LIKE查询**
   - 前缀匹配（可用索引）：10-50ms
   - 后缀/包含匹配（不可用索引）：100-500ms

5. **IN查询**
   - 10个值：< 10ms
   - 100个值：10-50ms
   - 1000个值：50-200ms

### 优化建议

1. **索引策略**
   - 主键查询：始终使用主键
   - 频繁查询列：添加索引
   - 范围查询：B-tree索引
   - LIKE前缀匹配：可利用索引

2. **查询优化**
   - 避免 SELECT *
   - 限制结果集大小
   - 使用EXPLAIN分析查询计划

### 所需能力（Capabilities）

- **基本查询**：`QueryCapability.WHERE_CLAUSE`
- **索引支持**：`IndexCapability.BTREE_INDEX`
- **LIKE操作**：`StringOperationCapability.PATTERN_MATCHING`
- **IN操作**：`QueryCapability.IN_CLAUSE`

### 测试数据特征

- **记录大小**：10-20 个字段，200-500 字节/条
- **数据分布**：均匀分布和倾斜分布
- **索引列**：整数、字符串、日期类型

### 报告格式

基准测试结果应包含：
- 查询响应时间（平均、中位数、P95、P99）
- 吞吐量（查询/秒）
- 索引使用情况
- 查询计划分析
- 与基准的对比
- 数据规模影响曲线
