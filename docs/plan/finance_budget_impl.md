# 财务系统：预算跟踪测试实施方案

## 1. 测试目标

本测试套件验证财务系统中预算管理和跟踪功能，确保用户能够有效地规划、监控和控制支出。预算跟踪是个人和企业财务管理的核心功能。

**核心验证点：**
- 预算的创建、修改和删除
- 支出分类和预算分配
- 实时预算使用情况跟踪
- 超支预警和通知
- 预算与实际对比报表
- 预算周期管理（月度、季度、年度）

**业务价值：**
- 帮助用户控制支出
- 提供财务规划工具
- 及时预警超支风险
- 支持财务决策分析

---

## 2. Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict, Any
from datetime import date
from rhosocial.activerecord import ActiveRecord

class IFinanceBudgetProvider(ABC):
    """财务预算跟踪测试的 Provider 接口。"""
    
    @abstractmethod
    def setup_budget_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Account
        Type[ActiveRecord],  # Budget
        Type[ActiveRecord],  # BudgetCategory
        Type[ActiveRecord],  # Transaction
        Type[ActiveRecord],  # BudgetAlert
        Type[ActiveRecord]   # BudgetReport
    ]:
        """
        设置预算跟踪相关的模型。
        
        Args:
            scenario: 测试场景名称
            
        Returns:
            包含 7 个模型类的元组：
            - User: 用户
            - Account: 账户
            - Budget: 预算
            - BudgetCategory: 预算分类
            - Transaction: 交易记录
            - BudgetAlert: 预算预警
            - BudgetReport: 预算报表
        """
        pass
    
    @abstractmethod
    def create_test_budget_data(
        self,
        user_count: int = 5,
        categories_per_user: int = 5,
        transactions_per_category: int = 20
    ) -> List[Dict[str, Any]]:
        """
        创建测试预算数据。
        
        Args:
            user_count: 用户数量
            categories_per_user: 每个用户的预算分类数
            transactions_per_category: 每个分类的交易数
            
        Returns:
            创建的预算数据信息列表
        """
        pass
    
    @abstractmethod
    def cleanup_budget_data(self, scenario: str):
        """清理预算测试数据。"""
        pass
```

---

## 3. 必要的夹具定义

```python
import pytest
from typing import Tuple, Type, List, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from rhosocial.activerecord import ActiveRecord

@pytest.fixture
def budget_models(request) -> Tuple[
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord],
    Type[ActiveRecord]
]:
    """
    提供预算跟踪相关的模型。
    
    Returns:
        (User, Account, Budget, BudgetCategory, Transaction, BudgetAlert, BudgetReport)
    """
    scenario = request.config.getoption("--scenario", default="local")
    provider = request.getfixturevalue("finance_budget_provider")
    
    models = provider.setup_budget_models(scenario)
    
    yield models
    
    provider.cleanup_budget_data(scenario)


@pytest.fixture
def test_budget_data(budget_models) -> List[Dict[str, Any]]:
    """
    创建测试预算数据。
    
    Returns:
        包含用户、账户、预算分类和交易的测试数据
    """
    User, Account, Budget, BudgetCategory, Transaction, BudgetAlert, BudgetReport = budget_models
    
    data = []
    
    # 用户 A: 完整的预算设置
    user_a = User(username="user_a", email="user_a@example.com")
    user_a.save()
    
    account_a = Account(
        user_id=user_a.id,
        account_number="ACC-A-001",
        account_type="checking",
        balance=5000.0,
        currency="USD"
    )
    account_a.save()
    
    # 本月预算
    today = date.today()
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    budget_a = Budget(
        user_id=user_a.id,
        account_id=account_a.id,
        name="Monthly Budget - December 2024",
        period_type="monthly",
        start_date=month_start,
        end_date=month_end,
        total_amount=3000.0,
        currency="USD",
        status="active"
    )
    budget_a.save()
    
    # 预算分类
    categories = [
        {"name": "Housing", "amount": 1000.0, "color": "#FF5733"},
        {"name": "Food", "amount": 600.0, "color": "#33FF57"},
        {"name": "Transportation", "amount": 400.0, "color": "#3357FF"},
        {"name": "Entertainment", "amount": 300.0, "color": "#FF33F5"},
        {"name": "Utilities", "amount": 200.0, "color": "#F5FF33"},
        {"name": "Healthcare", "amount": 300.0, "color": "#33FFF5"},
        {"name": "Miscellaneous", "amount": 200.0, "color": "#808080"}
    ]
    
    category_objects = []
    for cat_data in categories:
        category = BudgetCategory(
            budget_id=budget_a.id,
            name=cat_data["name"],
            allocated_amount=cat_data["amount"],
            color=cat_data["color"],
            alert_threshold=80.0  # 80% 时预警
        )
        category.save()
        category_objects.append(category)
    
    # 创建一些交易记录
    transactions = []
    
    # Housing - 接近预算
    for i in range(3):
        txn = Transaction(
            account_id=account_a.id,
            category_id=category_objects[0].id,  # Housing
            amount=-300.0,
            transaction_type="debit",
            description=f"Rent payment {i+1}",
            transaction_date=month_start + timedelta(days=i*5)
        )
        txn.save()
        transactions.append(txn)
    
    # Food - 部分使用
    for i in range(4):
        txn = Transaction(
            account_id=account_a.id,
            category_id=category_objects[1].id,  # Food
            amount=-100.0,
            transaction_type="debit",
            description=f"Grocery shopping {i+1}",
            transaction_date=month_start + timedelta(days=i*7)
        )
        txn.save()
        transactions.append(txn)
    
    # Transportation - 超支
    for i in range(5):
        txn = Transaction(
            account_id=account_a.id,
            category_id=category_objects[2].id,  # Transportation
            amount=-100.0,
            transaction_type="debit",
            description=f"Gas/Transport {i+1}",
            transaction_date=month_start + timedelta(days=i*4)
        )
        txn.save()
        transactions.append(txn)
    
    data.append({
        "user": user_a,
        "account": account_a,
        "budget": budget_a,
        "categories": category_objects,
        "transactions": transactions
    })
    
    return data


@pytest.fixture
def budget_alert_thresholds() -> Dict[str, float]:
    """提供预算预警阈值配置。"""
    return {
        "warning": 80.0,   # 80% 使用率时警告
        "critical": 95.0,  # 95% 使用率时严重警告
        "overspend": 100.0 # 超支时紧急预警
    }
```

---

## 4. 测试类和函数签名

### 4.1 预算创建和管理

```python
import pytest
from datetime import date, timedelta
from decimal import Decimal

@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestBudgetCreation:
    """测试预算创建和基本管理功能。"""
    
    def test_create_monthly_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试创建月度预算。
        
        验证点：
        1. 成功创建预算记录
        2. 设置正确的开始和结束日期
        3. 关联到用户和账户
        4. 初始状态为活跃
        """
        pass
    
    def test_create_quarterly_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试创建季度预算。
        
        验证点：
        1. 正确计算季度周期
        2. 分配合理的总金额
        """
        pass
    
    def test_create_yearly_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试创建年度预算。
        
        验证点：
        1. 设置年度周期
        2. 支持年度预算分配
        """
        pass
    
    def test_budget_with_categories(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试带分类的预算创建。
        
        验证点：
        1. 创建多个预算分类
        2. 分类金额总和不超过预算总额
        3. 每个分类有独立的分配额度
        """
        pass
    
    def test_update_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试更新预算。
        
        验证点：
        1. 修改预算总额
        2. 调整分类分配
        3. 更新后保持一致性
        """
        pass
    
    def test_delete_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试删除预算。
        
        验证点：
        1. 软删除或硬删除
        2. 关联数据的处理
        3. 历史数据保留
        """
        pass
    
    def test_budget_validation(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预算验证规则。
        
        验证点：
        1. 总额必须为正数
        2. 开始日期早于结束日期
        3. 分类总额不超过预算总额
        """
        pass


### 4.2 支出分类和跟踪

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestSpendingTracking:
    """测试支出跟踪功能。"""
    
    def test_track_spending_by_category(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试按分类跟踪支出。
        
        验证点：
        1. 交易自动归类到预算分类
        2. 实时更新已使用金额
        3. 计算剩余额度
        """
        pass
    
    def test_calculate_spending_percentage(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试计算支出百分比。
        
        验证点：
        1. 计算每个分类的使用率
        2. 计算总体预算使用率
        3. 百分比精度正确
        """
        pass
    
    def test_running_balance(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试运行余额计算。
        
        验证点：
        1. 计算累计支出
        2. 计算剩余预算
        3. 支持日期范围过滤
        """
        pass
    
    def test_transaction_categorization(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试交易分类。
        
        验证点：
        1. 手动指定分类
        2. 自动分类建议
        3. 分类修改影响预算计算
        """
        pass
    
    def test_uncategorized_transactions(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试未分类交易处理。
        
        验证点：
        1. 识别未分类交易
        2. 提示用户分类
        3. 未分类交易不计入预算
        """
        pass


### 4.3 超支预警

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestOverspendingAlerts:
    """测试超支预警功能。"""
    
    def test_warning_threshold_alert(
        self,
        budget_models,
        test_budget_data,
        budget_alert_thresholds
    ):
        """
        测试警告阈值预警。
        
        验证点：
        1. 使用率达到 80% 时触发警告
        2. 创建预警记录
        3. 发送通知（如果配置）
        """
        pass
    
    def test_critical_threshold_alert(
        self,
        budget_models,
        test_budget_data,
        budget_alert_thresholds
    ):
        """
        测试严重阈值预警。
        
        验证点：
        1. 使用率达到 95% 时触发严重警告
        2. 预警级别升级
        3. 更紧急的通知
        """
        pass
    
    def test_overspend_alert(
        self,
        budget_models,
        test_budget_data,
        budget_alert_thresholds
    ):
        """
        测试超支预警。
        
        验证点：
        1. 超出预算时触发紧急预警
        2. 标记为超支状态
        3. 阻止进一步支出（可选）
        """
        pass
    
    def test_alert_frequency_control(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预警频率控制。
        
        验证点：
        1. 避免重复预警
        2. 设置预警冷却期
        3. 状态变化时重新预警
        """
        pass
    
    def test_custom_alert_thresholds(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试自定义预警阈值。
        
        验证点：
        1. 用户可自定义阈值
        2. 不同分类可有不同阈值
        3. 阈值验证（0-100%）
        """
        pass
    
    def test_alert_notification(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预警通知。
        
        验证点：
        1. 生成通知消息
        2. 包含预警详情
        3. 支持多种通知方式（邮件、站内信等）
        """
        pass


### 4.4 预算报表

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestBudgetReports:
    """测试预算报表功能。"""
    
    def test_budget_vs_actual_report(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预算与实际对比报表。
        
        验证点：
        1. 显示预算分配额
        2. 显示实际支出
        3. 计算差异（正/负）
        4. 按分类分组
        """
        pass
    
    def test_spending_trend_report(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试支出趋势报表。
        
        验证点：
        1. 按时间展示支出趋势
        2. 支持日、周、月视图
        3. 识别支出模式
        """
        pass
    
    def test_category_breakdown_report(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试分类明细报表。
        
        验证点：
        1. 每个分类的详细支出
        2. 占总支出的百分比
        3. 排序功能（按金额、使用率等）
        """
        pass
    
    def test_monthly_summary_report(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试月度汇总报表。
        
        验证点：
        1. 当月总支出
        2. 各分类使用情况
        3. 超支分类标记
        4. 月度趋势对比
        """
        pass
    
    def test_yearly_comparison_report(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试年度对比报表。
        
        验证点：
        1. 同比支出变化
        2. 各月度支出对比
        3. 年度预算执行率
        """
        pass
    
    def test_export_report(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试报表导出。
        
        验证点：
        1. 导出为 CSV
        2. 导出为 PDF
        3. 包含图表和数据
        """
        pass


### 4.5 预算周期管理

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestBudgetPeriod:
    """测试预算周期管理。"""
    
    def test_budget_rollover(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预算结转。
        
        验证点：
        1. 未使用的预算可结转到下期
        2. 超支金额影响下期预算
        3. 结转规则可配置
        """
        pass
    
    def test_budget_recurrence(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预算循环。
        
        验证点：
        1. 自动创建下一周期预算
        2. 复制分类和金额设置
        3. 支持调整
        """
        pass
    
    def test_budget_archival(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预算归档。
        
        验证点：
        1. 过期预算自动归档
        2. 归档数据仍可查询
        3. 历史对比功能
        """
        pass
    
    def test_mid_period_adjustment(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试周期中调整。
        
        验证点：
        1. 支持周期中修改预算
        2. 记录调整历史
        3. 调整影响后续计算
        """
        pass


### 4.6 预算统计和分析

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestBudgetStatistics:
    """测试预算统计和分析功能。"""
    
    def test_overall_budget_utilization(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试整体预算利用率。
        
        验证点：
        1. 计算总体使用率
        2. 分类使用率分布
        3. 识别高/低使用分类
        """
        pass
    
    def test_spending_patterns(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试支出模式分析。
        
        验证点：
        1. 识别固定支出
        2. 识别可变支出
        3. 支出周期性分析
        """
        pass
    
    def test_budget_performance_metrics(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预算绩效指标。
        
        验证点：
        1. 预算执行率
        2. 超支频率
        3. 节余率
        4. 预算准确性
        """
        pass
    
    def test_category_comparison(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试分类对比分析。
        
        验证点：
        1. 多个预算周期的同一分类对比
        2. 同一周期的不同分类对比
        3. 趋势识别
        """
        pass
    
    def test_predictive_analysis(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试预测分析。
        
        验证点：
        1. 基于历史数据预测支出
        2. 预测超支风险
        3. 预算建议
        """
        pass


### 4.7 多用户和权限

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
@pytest.mark.integration
class TestBudgetPermissions:
    """测试预算权限管理。"""
    
    def test_personal_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试个人预算。
        
        验证点：
        1. 用户只能访问自己的预算
        2. 预算隔离
        """
        pass
    
    def test_shared_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试共享预算。
        
        验证点：
        1. 多个用户共享一个预算
        2. 权限控制（查看、编辑、管理）
        3. 协作编辑
        """
        pass
    
    def test_family_budget(
        self,
        budget_models,
        test_budget_data
    ):
        """
        测试家庭预算。
        
        验证点：
        1. 家庭成员共享预算
        2. 父预算和子预算
        3. 层级权限
        """
        pass
```

---

## 5. 功能覆盖范围

### 5.1 核心功能
- ✅ 预算创建和管理（月度、季度、年度）
- ✅ 预算分类和分配
- ✅ 支出跟踪和分类
- ✅ 实时预算使用情况
- ✅ 超支预警系统
- ✅ 预算报表和分析
- ✅ 预算周期管理

### 5.2 高级功能
- ✅ 预算结转和循环
- ✅ 支出模式分析
- ✅ 预测性分析
- ✅ 多用户共享预算
- ✅ 自定义预警阈值

### 5.3 所需能力
```python
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    AggregateFunctionCapability,
    WindowFunctionCapability,
    DateFunctionCapability
)

# 必需能力
required_capabilities = [
    (CapabilityCategory.AGGREGATE, AggregateFunctionCapability.SUM),
    (CapabilityCategory.AGGREGATE, AggregateFunctionCapability.COUNT),
    (CapabilityCategory.DATE, DateFunctionCapability.DATE_TRUNC),
    (CapabilityCategory.DATE, DateFunctionCapability.DATE_PART)
]

# 可选能力（用于高级分析）
optional_capabilities = [
    (CapabilityCategory.WINDOW_FUNCTIONS, WindowFunctionCapability.ROW_NUMBER),
    (CapabilityCategory.WINDOW_FUNCTIONS, WindowFunctionCapability.LAG),
    (CapabilityCategory.CTE, CTECapability.BASIC_CTE)
]
```

---

## 6. 测试数据规模

### 6.1 基础测试（small_scale）
- 用户数: 5
- 预算数: 10
- 预算分类: 30-50
- 交易记录: 100-500
- **用途**: 功能验证

### 6.2 中等规模测试（medium_scale）
- 用户数: 100
- 预算数: 200-500
- 预算分类: 1000-2000
- 交易记录: 10000-50000
- **用途**: 性能验证、报表测试

### 6.3 大规模测试（large_scale）
- 用户数: 10000
- 预算数: 20000-50000
- 预算分类: 100000+
- 交易记录: 1000000+
- **用途**: 扩展性测试、大数据分析

---

## 7. 实施注意事项

### 7.1 数据一致性
- 预算分类总额 ≤ 预算总额
- 交易归类后实时更新统计
- 处理未分类交易
- 支持交易重分类

### 7.2 性能优化
- 预算统计使用聚合查询
- 缓存常用报表数据
- 索引优化（用户ID、日期、分类）
- 增量更新统计数据

### 7.3 预警机制
- 异步预警处理
- 避免重复预警
- 可配置预警规则
- 多渠道通知

### 7.4 报表生成
- 支持多种时间维度
- 数据可视化准备
- 导出功能
- 历史数据对比

---

## 8. 性能目标

- 预算创建: < 100ms
- 支出分类统计: < 200ms
- 预警检查: < 500ms
- 报表生成（月度）: < 2s
- 报表生成（年度）: < 10s

---

本实施方案提供了财务系统预算跟踪测试的完整框架。