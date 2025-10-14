# 项目管理 - 时间跟踪测试实施方案

## 测试目标

验证时间跟踪系统，包括时间记录、计时器控制、工时表生成、计费时间计算、时间报表和时间审批等功能。

## Provider 接口定义

### ITimeTrackingProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class ITimeTrackingProvider(ABC):
    """时间跟踪测试数据提供者接口"""
    
    @abstractmethod
    def setup_timetracking_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Project
        Type[ActiveRecord],  # Task
        Type[ActiveRecord],  # TimeEntry
        Type[ActiveRecord],  # Timer
        Type[ActiveRecord],  # Timesheet
        Type[ActiveRecord],  # TimesheetApproval
        Type[ActiveRecord]   # BillingRate
    ]:
        """设置时间跟踪相关模型"""
        pass
    
    @abstractmethod
    def create_time_entries(
        self,
        user_count: int,
        entries_per_user_range: Tuple[int, int]
    ) -> List[Dict]:
        """创建时间记录数据"""
        pass
    
    @abstractmethod
    def create_timesheets(
        self,
        user_count: int,
        week_count: int
    ) -> List[Dict]:
        """创建工时表数据"""
        pass
    
    @abstractmethod
    def cleanup_timetracking_data(self, scenario: str):
        """清理时间跟踪测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def timetracking_models(request):
    """提供时间跟踪模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_time_tracking_provider()
    
    models = provider.setup_timetracking_models(scenario)
    yield models
    
    provider.cleanup_timetracking_data(scenario)

@pytest.fixture
def User(timetracking_models):
    """用户模型"""
    return timetracking_models[0]

@pytest.fixture
def Project(timetracking_models):
    """项目模型"""
    return timetracking_models[1]

@pytest.fixture
def Task(timetracking_models):
    """任务模型"""
    return timetracking_models[2]

@pytest.fixture
def TimeEntry(timetracking_models):
    """时间记录模型"""
    return timetracking_models[3]

@pytest.fixture
def Timer(timetracking_models):
    """计时器模型"""
    return timetracking_models[4]

@pytest.fixture
def Timesheet(timetracking_models):
    """工时表模型"""
    return timetracking_models[5]

@pytest.fixture
def TimesheetApproval(timetracking_models):
    """工时表审批模型"""
    return timetracking_models[6]

@pytest.fixture
def BillingRate(timetracking_models):
    """计费费率模型"""
    return timetracking_models[7]

@pytest.fixture
def test_user(User):
    """测试用户"""
    user = User(
        username="test_user",
        email="user@test.com",
        is_active=True
    )
    user.save()
    return user

@pytest.fixture
def test_project(Project):
    """测试项目"""
    project = Project(
        name="Test Project",
        is_active=True
    )
    project.save()
    return project

@pytest.fixture
def test_task(Task, test_project):
    """测试任务"""
    task = Task(
        title="Test Task",
        project_id=test_project.id,
        status="in_progress"
    )
    task.save()
    return task
```

## 测试类和函数签名

### TestTimeEntryLogging - 时间记录测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimeEntryLogging:
    """时间记录测试"""
    
    def test_create_time_entry(self, TimeEntry, test_user, test_task):
        """测试创建时间记录"""
        pass
    
    def test_time_entry_with_duration(self, TimeEntry, test_user, test_task):
        """测试带时长的时间记录"""
        pass
    
    def test_time_entry_with_start_end(self, TimeEntry, test_user, test_task):
        """测试带起止时间的记录"""
        pass
    
    def test_time_entry_description(self, TimeEntry, test_user, test_task):
        """测试时间记录描述"""
        pass
    
    def test_time_entry_validation(self, TimeEntry, test_user, test_task):
        """测试时间记录验证"""
        pass
    
    def test_edit_time_entry(self, TimeEntry, test_user, test_task):
        """测试编辑时间记录"""
        pass
    
    def test_delete_time_entry(self, TimeEntry, test_user):
        """测试删除时间记录"""
        pass
```

### TestTimerControl - 计时器控制测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimerControl:
    """计时器控制测试"""
    
    def test_start_timer(self, Timer, test_user, test_task):
        """测试启动计时器"""
        pass
    
    def test_stop_timer(self, Timer, TimeEntry, test_user, test_task):
        """测试停止计时器"""
        pass
    
    def test_pause_resume_timer(self, Timer, test_user, test_task):
        """测试暂停/恢复计时器"""
        pass
    
    def test_timer_duration_calculation(self, Timer, test_user, test_task):
        """测试计时器时长计算"""
        pass
    
    def test_multiple_timers_prevention(self, Timer, test_user):
        """测试防止多个活动计时器"""
        pass
    
    def test_timer_to_time_entry(self, Timer, TimeEntry, test_user):
        """测试计时器转为时间记录"""
        pass
    
    def test_running_timer_query(self, Timer, test_user):
        """测试查询运行中的计时器"""
        pass
```

### TestTimesheetGeneration - 工时表生成测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimesheetGeneration:
    """工时表生成测试"""
    
    def test_generate_weekly_timesheet(self, Timesheet, TimeEntry, test_user):
        """测试生成周工时表"""
        pass
    
    def test_generate_monthly_timesheet(self, Timesheet, TimeEntry, test_user):
        """测试生成月工时表"""
        pass
    
    def test_timesheet_summary(self, Timesheet, TimeEntry, test_user):
        """测试工时表摘要"""
        pass
    
    def test_timesheet_by_project(self, Timesheet, TimeEntry, Project, test_user):
        """测试按项目分组的工时表"""
        pass
    
    def test_timesheet_by_task(self, Timesheet, TimeEntry, Task, test_user):
        """测试按任务分组的工时表"""
        pass
    
    def test_empty_timesheet(self, Timesheet, test_user):
        """测试空工时表"""
        pass
```

### TestBillableHours - 计费时间测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestBillableHours:
    """计费时间测试"""
    
    def test_mark_as_billable(self, TimeEntry, test_user, test_task):
        """测试标记为可计费"""
        pass
    
    def test_mark_as_non_billable(self, TimeEntry, test_user, test_task):
        """测试标记为不可计费"""
        pass
    
    def test_billable_hours_calculation(self, TimeEntry, test_user):
        """测试计费时间计算"""
        pass
    
    def test_billable_rate_application(self, TimeEntry, BillingRate, test_user):
        """测试应用计费费率"""
        pass
    
    def test_project_level_billing(self, Project, TimeEntry, BillingRate):
        """测试项目级别计费"""
        pass
    
    def test_user_level_billing(self, User, TimeEntry, BillingRate):
        """测试用户级别计费"""
        pass
    
    def test_billable_amount_calculation(self, TimeEntry, BillingRate, test_user):
        """测试计费金额计算"""
        pass
```

### TestTimeReports - 时间报表测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
@requires_capabilities(
    (CapabilityCategory.WINDOW_FUNCTIONS, WindowFunctionCapability.ROW_NUMBER),
    (CapabilityCategory.AGGREGATE_FUNCTIONS, AggregateFunctionCapability.SUM)
)
class TestTimeReports:
    """时间报表测试"""
    
    def test_user_time_summary(self, TimeEntry, test_user):
        """测试用户时间汇总"""
        pass
    
    def test_project_time_summary(self, TimeEntry, Project):
        """测试项目时间汇总"""
        pass
    
    def test_daily_time_report(self, TimeEntry, test_user):
        """测试日时间报表"""
        pass
    
    def test_weekly_time_report(self, TimeEntry, test_user):
        """测试周时间报表"""
        pass
    
    def test_monthly_time_report(self, TimeEntry, test_user):
        """测试月时间报表"""
        pass
    
    def test_team_time_comparison(self, TimeEntry, User):
        """测试团队时间对比"""
        pass
    
    def test_time_distribution_chart(self, TimeEntry, Project, test_user):
        """测试时间分布图数据"""
        pass
```

### TestTimesheetApproval - 工时表审批测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
@pytest.mark.workflow
class TestTimesheetApproval:
    """工时表审批测试"""
    
    def test_submit_timesheet(self, Timesheet, TimesheetApproval, test_user):
        """测试提交工时表"""
        pass
    
    def test_approve_timesheet(self, Timesheet, TimesheetApproval, User):
        """测试批准工时表"""
        pass
    
    def test_reject_timesheet(self, Timesheet, TimesheetApproval, User):
        """测试拒绝工时表"""
        pass
    
    def test_request_revision(self, Timesheet, TimesheetApproval, User):
        """测试请求修订"""
        pass
    
    def test_approval_workflow(self, Timesheet, TimesheetApproval, User):
        """测试审批工作流"""
        pass
    
    def test_approval_notification(self, Timesheet, TimesheetApproval, User):
        """测试审批通知"""
        pass
    
    def test_bulk_approval(self, Timesheet, TimesheetApproval, User):
        """测试批量审批"""
        pass
```

### TestOvertime - 加班时间测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestOvertime:
    """加班时间测试"""
    
    def test_detect_overtime(self, TimeEntry, test_user):
        """测试检测加班时间"""
        pass
    
    def test_overtime_calculation(self, TimeEntry, test_user):
        """测试加班时间计算"""
        pass
    
    def test_overtime_rate(self, TimeEntry, BillingRate, test_user):
        """测试加班费率"""
        pass
    
    def test_weekend_hours(self, TimeEntry, test_user):
        """测试周末工时"""
        pass
    
    def test_holiday_hours(self, TimeEntry, test_user):
        """测试节假日工时"""
        pass
```

### TestTimeTracking Integrations - 时间跟踪集成测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimeTrackingIntegrations:
    """时间跟踪集成测试"""
    
    def test_task_time_rollup(self, Task, TimeEntry):
        """测试任务时间汇总"""
        pass
    
    def test_project_time_rollup(self, Project, TimeEntry):
        """测试项目时间汇总"""
        pass
    
    def test_budget_tracking(self, Project, TimeEntry, BillingRate):
        """测试预算跟踪"""
        pass
    
    def test_budget_alerts(self, Project, TimeEntry, BillingRate):
        """测试预算预警"""
        pass
    
    def test_time_vs_estimate(self, Task, TimeEntry):
        """测试实际时间与估算对比"""
        pass
```

### TestTimeStatistics - 时间统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimeStatistics:
    """时间统计测试"""
    
    def test_total_hours_logged(self, TimeEntry, test_user):
        """测试总记录时间"""
        pass
    
    def test_average_daily_hours(self, TimeEntry, test_user):
        """测试日均工时"""
        pass
    
    def test_productivity_metrics(self, TimeEntry, Task, test_user):
        """测试生产力指标"""
        pass
    
    def test_time_utilization_rate(self, TimeEntry, test_user):
        """测试时间利用率"""
        pass
    
    def test_most_time_consuming_projects(self, Project, TimeEntry):
        """测试最耗时项目"""
        pass
    
    def test_time_tracking_compliance(self, TimeEntry, User):
        """测试时间记录合规性"""
        pass
```

### TestTimeEntryExport - 时间记录导出测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimeEntryExport:
    """时间记录导出测试"""
    
    def test_export_to_csv(self, TimeEntry, test_user):
        """测试导出为CSV"""
        pass
    
    def test_export_to_excel(self, TimeEntry, test_user):
        """测试导出为Excel"""
        pass
    
    def test_export_with_filters(self, TimeEntry, test_user):
        """测试带过滤器的导出"""
        pass
    
    def test_export_date_range(self, TimeEntry, test_user):
        """测试按日期范围导出"""
        pass
```

### TestTimePerformance - 时间跟踪性能测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTimePerformance:
    """时间跟踪性能测试"""
    
    def test_time_entry_creation_speed(self, TimeEntry, test_user, test_task):
        """测试时间记录创建速度"""
        pass
    
    def test_timesheet_generation_performance(self, Timesheet, TimeEntry):
        """测试工时表生成性能"""
        pass
    
    def test_large_timesheet_handling(self, TimeEntry, test_user):
        """测试大工时表处理（1000+记录）"""
        pass
    
    def test_report_generation_speed(self, TimeEntry, Project):
        """测试报表生成速度"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **时间记录**
   - 创建记录
   - 时长记录
   - 起止时间
   - 记录描述
   - 数据验证
   - 编辑/删除

2. **计时器控制**
   - 启动计时器
   - 停止计时器
   - 暂停/恢复
   - 时长计算
   - 多计时器防止
   - 转为记录
   - 查询运行中计时器

3. **工时表生成**
   - 周工时表
   - 月工时表
   - 工时表摘要
   - 按项目分组
   - 按任务分组
   - 空工时表

4. **计费时间**
   - 可计费标记
   - 不可计费标记
   - 计费时间计算
   - 费率应用
   - 项目级计费
   - 用户级计费
   - 金额计算

5. **时间报表**
   - 用户时间汇总
   - 项目时间汇总
   - 日/周/月报表
   - 团队对比
   - 时间分布图

6. **工时表审批**
   - 提交工时表
   - 批准/拒绝
   - 请求修订
   - 审批工作流
   - 审批通知
   - 批量审批

7. **加班时间**
   - 加班检测
   - 加班计算
   - 加班费率
   - 周末工时
   - 节假日工时

8. **集成功能**
   - 任务时间汇总
   - 项目时间汇总
   - 预算跟踪
   - 预算预警
   - 时间与估算对比

9. **时间统计**
   - 总时间
   - 日均工时
   - 生产力指标
   - 时间利用率
   - 最耗时项目
   - 记录合规性

10. **数据导出**
    - CSV导出
    - Excel导出
    - 带过滤器导出
    - 日期范围导出

11. **性能优化**
    - 创建速度
    - 工时表生成
    - 大数据处理
    - 报表生成

### 所需能力（Capabilities）

- **窗口函数**：累计时间、时间排名
- **聚合函数**：时间汇总、统计计算
- **关系加载**：时间记录->任务->项目
- **查询优化**：大量时间记录的报表查询

### 测试数据规模

- 用户：5-20 个用户
- 时间记录：每个用户 50-500 条记录
- 工时表：每个用户 10-50 周的工时表
- 项目：5-20 个项目
- 任务：20-100 个任务

### 性能预期

- 时间记录创建：< 50ms
- 计时器启动/停止：< 30ms
- 工时表生成（1周）：< 200ms
- 工时表生成（1月）：< 500ms
- 时间报表（1个月）：< 1s
- 审批操作：< 100ms
- 大工时表（1000条）：< 2s
- 数据导出（500条）：< 1s
