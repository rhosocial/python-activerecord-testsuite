# 财务系统 - 账户操作测试实施方案

## 测试目标

验证账户操作系统，包括账户创建、存取款、余额计算、交易历史、对账单生成和账户锁定等核心财务功能。

## Provider 接口定义

### IAccountOperationsProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from decimal import Decimal
from rhosocial.activerecord import ActiveRecord

class IAccountOperationsProvider(ABC):
    """账户操作测试数据提供者接口"""
    
    @abstractmethod
    def setup_account_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Account
        Type[ActiveRecord],  # Transaction
        Type[ActiveRecord],  # Balance
        Type[ActiveRecord],  # Statement
        Type[ActiveRecord],  # AccountLock
        Type[ActiveRecord]   # TransactionLog
    ]:
        """设置账户操作相关模型"""
        pass
    
    @abstractmethod
    def create_test_accounts(
        self,
        user_count: int,
        accounts_per_user: int,
        initial_balance_range: Tuple[Decimal, Decimal]
    ) -> List[Dict]:
        """创建测试账户"""
        pass
    
    @abstractmethod
    def create_transactions(
        self,
        account_count: int,
        transactions_per_account: int
    ) -> List[Dict]:
        """创建交易数据"""
        pass
    
    @abstractmethod
    def cleanup_account_data(self, scenario: str):
        """清理账户测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def account_models(request):
    """提供账户操作模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_account_operations_provider()
    
    models = provider.setup_account_models(scenario)
    yield models
    
    provider.cleanup_account_data(scenario)

@pytest.fixture
def User(account_models):
    """用户模型"""
    return account_models[0]

@pytest.fixture
def Account(account_models):
    """账户模型"""
    return account_models[1]

@pytest.fixture
def Transaction(account_models):
    """交易模型"""
    return account_models[2]

@pytest.fixture
def Balance(account_models):
    """余额模型"""
    return account_models[3]

@pytest.fixture
def Statement(account_models):
    """对账单模型"""
    return account_models[4]

@pytest.fixture
def AccountLock(account_models):
    """账户锁定模型"""
    return account_models[5]

@pytest.fixture
def TransactionLog(account_models):
    """交易日志模型"""
    return account_models[6]

@pytest.fixture
def test_user(User):
    """测试用户"""
    user = User(
        username="test_user",
        email="user@test.com",
        is_verified=True,
        is_active=True
    )
    user.save()
    return user

@pytest.fixture
def test_account(Account, test_user):
    """测试账户"""
    account = Account(
        user_id=test_user.id,
        account_number="1234567890",
        account_type="checking",
        currency="USD",
        status="active"
    )
    account.save()
    return account
```

## 测试类和函数签名

### TestAccountCreation - 账户创建测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestAccountCreation:
    """账户创建测试"""
    
    def test_create_checking_account(self, Account, test_user):
        """测试创建支票账户"""
        pass
    
    def test_create_savings_account(self, Account, test_user):
        """测试创建储蓄账户"""
        pass
    
    def test_account_number_generation(self, Account, test_user):
        """测试账户号生成"""
        pass
    
    def test_account_validation(self, Account, test_user):
        """测试账户数据验证"""
        pass
    
    def test_multiple_accounts_per_user(self, Account, test_user):
        """测试用户多账户"""
        pass
    
    def test_account_currency(self, Account, test_user):
        """测试账户货币"""
        pass
    
    def test_initial_balance(self, Account, Balance, test_user):
        """测试初始余额"""
        pass
```

### TestDeposit - 存款测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestDeposit:
    """存款测试"""
    
    def test_deposit_funds(self, Account, Transaction, Balance, test_account):
        """测试存款"""
        pass
    
    def test_deposit_validation(self, Account, Transaction, test_account):
        """测试存款验证"""
        pass
    
    def test_negative_deposit_prevention(self, Account, Transaction, test_account):
        """测试防止负数存款"""
        pass
    
    def test_deposit_with_description(self, Transaction, test_account):
        """测试带描述的存款"""
        pass
    
    def test_deposit_balance_update(self, Account, Transaction, Balance, test_account):
        """测试存款后余额更新"""
        pass
    
    def test_deposit_transaction_record(self, Transaction, TransactionLog, test_account):
        """测试存款交易记录"""
        pass
```

### TestWithdrawal - 取款测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestWithdrawal:
    """取款测试"""
    
    def test_withdraw_funds(self, Account, Transaction, Balance, test_account):
        """测试取款"""
        pass
    
    def test_insufficient_funds(self, Account, Transaction, test_account):
        """测试余额不足（应失败）"""
        pass
    
    def test_withdrawal_limit(self, Account, Transaction, test_account):
        """测试取款限额"""
        pass
    
    def test_withdrawal_balance_update(self, Account, Transaction, Balance, test_account):
        """测试取款后余额更新"""
        pass
    
    def test_overdraft_prevention(self, Account, Transaction, test_account):
        """测试防止透支"""
        pass
```

### TestBalanceCalculation - 余额计算测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestBalanceCalculation:
    """余额计算测试"""
    
    def test_calculate_current_balance(self, Account, Balance, Transaction, test_account):
        """测试计算当前余额"""
        pass
    
    def test_available_balance(self, Account, Balance, test_account):
        """测试可用余额"""
        pass
    
    def test_pending_balance(self, Account, Balance, Transaction, test_account):
        """测试待处理余额"""
        pass
    
    def test_balance_after_multiple_transactions(self, Account, Transaction, Balance):
        """测试多笔交易后的余额"""
        pass
    
    def test_balance_consistency(self, Account, Transaction, Balance, test_account):
        """测试余额一致性"""
        pass
```

### TestTransactionHistory - 交易历史测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestTransactionHistory:
    """交易历史测试"""
    
    def test_get_transaction_history(self, Transaction, test_account):
        """测试获取交易历史"""
        pass
    
    def test_filter_by_date_range(self, Transaction, test_account):
        """测试按日期范围筛选"""
        pass
    
    def test_filter_by_transaction_type(self, Transaction, test_account):
        """测试按交易类型筛选"""
        pass
    
    def test_transaction_pagination(self, Transaction, test_account):
        """测试交易分页"""
        pass
    
    def test_transaction_search(self, Transaction, test_account):
        """测试交易搜索"""
        pass
    
    def test_transaction_sorting(self, Transaction, test_account):
        """测试交易排序"""
        pass
```

### TestStatementGeneration - 对账单生成测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestStatementGeneration:
    """对账单生成测试"""
    
    def test_generate_monthly_statement(self, Statement, Account, Transaction, test_account):
        """测试生成月对账单"""
        pass
    
    def test_statement_summary(self, Statement, Transaction, test_account):
        """测试对账单摘要"""
        pass
    
    def test_statement_transaction_list(self, Statement, Transaction, test_account):
        """测试对账单交易列表"""
        pass
    
    def test_opening_closing_balance(self, Statement, Balance, test_account):
        """测试期初期末余额"""
        pass
    
    def test_statement_period(self, Statement, test_account):
        """测试对账单周期"""
        pass
    
    def test_statement_export(self, Statement, test_account):
        """测试对账单导出（PDF/CSV）"""
        pass
```

### TestAccountLocking - 账户锁定测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestAccountLocking:
    """账户锁定测试"""
    
    def test_lock_account(self, Account, AccountLock, test_account):
        """测试锁定账户"""
        pass
    
    def test_unlock_account(self, Account, AccountLock, test_account):
        """测试解锁账户"""
        pass
    
    def test_locked_account_transactions(self, Account, Transaction, test_account):
        """测试锁定账户的交易（应失败）"""
        pass
    
    def test_lock_reason(self, AccountLock, test_account):
        """测试锁定原因"""
        pass
    
    def test_auto_lock_on_suspicious_activity(self, Account, Transaction, AccountLock):
        """测试可疑活动自动锁定"""
        pass
    
    def test_temporary_lock(self, Account, AccountLock, test_account):
        """测试临时锁定"""
        pass
```

### TestTransactionReversal - 交易撤销测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestTransactionReversal:
    """交易撤销测试"""
    
    def test_reverse_transaction(self, Transaction, Balance, test_account):
        """测试撤销交易"""
        pass
    
    def test_reversal_creates_offsetting_transaction(self, Transaction, test_account):
        """测试撤销创建抵消交易"""
        pass
    
    def test_balance_after_reversal(self, Account, Transaction, Balance, test_account):
        """测试撤销后余额"""
        pass
    
    def test_reversal_authorization(self, Transaction, User):
        """测试撤销权限"""
        pass
    
    def test_reversal_time_limit(self, Transaction, test_account):
        """测试撤销时限"""
        pass
```

### TestAccountClosure - 账户关闭测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestAccountClosure:
    """账户关闭测试"""
    
    def test_close_account(self, Account, test_account):
        """测试关闭账户"""
        pass
    
    def test_close_with_zero_balance(self, Account, Balance, test_account):
        """测试零余额关闭"""
        pass
    
    def test_cannot_close_with_balance(self, Account, Balance, test_account):
        """测试有余额不能关闭"""
        pass
    
    def test_closed_account_transactions(self, Account, Transaction, test_account):
        """测试已关闭账户的交易（应失败）"""
        pass
    
    def test_reopen_account(self, Account, test_account):
        """测试重新开户"""
        pass
```

### TestAccountFees - 账户费用测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestAccountFees:
    """账户费用测试"""
    
    def test_monthly_maintenance_fee(self, Account, Transaction, test_account):
        """测试月维护费"""
        pass
    
    def test_overdraft_fee(self, Account, Transaction, test_account):
        """测试透支费"""
        pass
    
    def test_atm_fee(self, Transaction, test_account):
        """测试ATM手续费"""
        pass
    
    def test_fee_waiver(self, Account, Transaction):
        """测试费用减免"""
        pass
```

### TestInterestCalculation - 利息计算测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestInterestCalculation:
    """利息计算测试"""
    
    def test_calculate_daily_interest(self, Account, Balance):
        """测试计算日利息"""
        pass
    
    def test_compound_interest(self, Account, Balance, Transaction):
        """测试复利计算"""
        pass
    
    def test_interest_posting(self, Account, Transaction, Balance):
        """测试利息入账"""
        pass
    
    def test_interest_rate_change(self, Account, Balance):
        """测试利率变更"""
        pass
```

### TestAccountStatistics - 账户统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_finance
class TestAccountStatistics:
    """账户统计测试"""
    
    def test_account_summary(self, Account, Transaction, Balance):
        """测试账户摘要统计"""
        pass
    
    def test_transaction_volume(self, Transaction, test_account):
        """测试交易量统计"""
        pass
    
    def test_average_balance(self, Balance, test_account):
        """测试平均余额"""
        pass
    
    def test_account_activity_report(self, Account, Transaction):
        """测试账户活动报表"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **账户创建**
   - 支票账户
   - 储蓄账户
   - 账号生成
   - 数据验证
   - 多账户
   - 货币设置
   - 初始余额

2. **存款操作**
   - 存款
   - 存款验证
   - 负数防止
   - 存款描述
   - 余额更新
   - 交易记录

3. **取款操作**
   - 取款
   - 余额不足检查
   - 取款限额
   - 余额更新
   - 透支防止

4. **余额计算**
   - 当前余额
   - 可用余额
   - 待处理余额
   - 多交易余额
   - 余额一致性

5. **交易历史**
   - 交易历史
   - 日期筛选
   - 类型筛选
   - 交易分页
   - 交易搜索
   - 交易排序

6. **对账单生成**
   - 月对账单
   - 对账单摘要
   - 交易列表
   - 期初期末余额
   - 对账单周期
   - 对账单导出

7. **账户锁定**
   - 锁定账户
   - 解锁账户
   - 锁定交易限制
   - 锁定原因
   - 自动锁定
   - 临时锁定

8. **交易撤销**
   - 撤销交易
   - 抵消交易
   - 撤销后余额
   - 撤销权限
   - 撤销时限

9. **账户关闭**
   - 关闭账户
   - 零余额关闭
   - 有余额限制
   - 关闭后交易限制
   - 重新开户

10. **账户费用**
    - 维护费
    - 透支费
    - ATM费
    - 费用减免

11. **利息计算**
    - 日利息
    - 复利
    - 利息入账
    - 利率变更

12. **账户统计**
    - 账户摘要
    - 交易量
    - 平均余额
    - 活动报表

### 所需能力（Capabilities）

- **事务支持（CRITICAL）**：存取款的ACID特性必须保证
- **聚合函数**：余额计算、统计分析
- **关系加载**：账户->交易->余额
- **精确数值**：Decimal类型支持，防止浮点误差

### 测试数据规模

- 用户：10-50 个用户
- 账户：每个用户 1-3 个账户
- 交易：每个账户 50-500 笔交易
- 对账单：每个账户 12-24 个月对账单

### 性能预期

- 账户创建：< 100ms
- 存款/取款：< 100ms（包含事务）
- 余额查询：< 10ms
- 交易历史（100条）：< 150ms
- 对账单生成：< 500ms
- 账户锁定：< 50ms
- 交易撤销：< 200ms（包含事务）
