# 项目管理 - 项目规划测试实施方案

## 测试目标

验证项目规划系统，包括项目创建、里程碑管理、任务分解、任务分配、依赖跟踪和甘特图数据生成等功能。

## Provider 接口定义

### IProjectPlanningProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class IProjectPlanningProvider(ABC):
    """项目规划测试数据提供者接口"""
    
    @abstractmethod
    def setup_planning_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Project
        Type[ActiveRecord],  # Milestone
        Type[ActiveRecord],  # Task
        Type[ActiveRecord],  # TaskDependency
        Type[ActiveRecord],  # TaskAssignment
        Type[ActiveRecord],  # ProjectTeam
        Type[ActiveRecord]   # ProjectTimeline
    ]:
        """设置项目规划相关模型"""
        pass
    
    @abstractmethod
    def create_project_structure(
        self,
        project_count: int,
        milestones_per_project: int,
        tasks_per_milestone: int
    ) -> List[Dict]:
        """创建项目结构数据"""
        pass
    
    @abstractmethod
    def create_team_members(
        self,
        member_count: int
    ) -> List[Dict]:
        """创建团队成员"""
        pass
    
    @abstractmethod
    def create_task_dependencies(
        self,
        task_count: int,
        dependency_ratio: float
    ) -> List[Dict]:
        """创建任务依赖关系"""
        pass
    
    @abstractmethod
    def cleanup_planning_data(self, scenario: str):
        """清理项目规划测试数据"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def planning_models(request):
    """提供项目规划模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_project_planning_provider()
    
    models = provider.setup_planning_models(scenario)
    yield models
    
    provider.cleanup_planning_data(scenario)

@pytest.fixture
def User(planning_models):
    """用户模型"""
    return planning_models[0]

@pytest.fixture
def Project(planning_models):
    """项目模型"""
    return planning_models[1]

@pytest.fixture
def Milestone(planning_models):
    """里程碑模型"""
    return planning_models[2]

@pytest.fixture
def Task(planning_models):
    """任务模型"""
    return planning_models[3]

@pytest.fixture
def TaskDependency(planning_models):
    """任务依赖模型"""
    return planning_models[4]

@pytest.fixture
def TaskAssignment(planning_models):
    """任务分配模型"""
    return planning_models[5]

@pytest.fixture
def ProjectTeam(planning_models):
    """项目团队模型"""
    return planning_models[6]

@pytest.fixture
def ProjectTimeline(planning_models):
    """项目时间线模型"""
    return planning_models[7]

@pytest.fixture
def test_manager(User):
    """测试项目经理"""
    manager = User(
        username="test_manager",
        email="manager@test.com",
        role="project_manager",
        is_active=True
    )
    manager.save()
    return manager

@pytest.fixture
def test_team_members(User):
    """测试团队成员"""
    members = []
    for i in range(5):
        member = User(
            username=f"team_member_{i}",
            email=f"member{i}@test.com",
            role="team_member",
            is_active=True
        )
        member.save()
        members.append(member)
    return members

@pytest.fixture
def test_project(Project, test_manager):
    """测试项目"""
    project = Project(
        name="Test Project",
        description="Test project description",
        manager_id=test_manager.id,
        status="active",
        start_date="2025-01-01",
        end_date="2025-12-31"
    )
    project.save()
    return project
```

## 测试类和函数签名

### TestProjectCreation - 项目创建测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestProjectCreation:
    """项目创建测试"""
    
    def test_create_project(self, Project, test_manager):
        """测试创建项目"""
        pass
    
    def test_project_with_dates(self, Project, test_manager):
        """测试带起止日期的项目"""
        pass
    
    def test_project_with_budget(self, Project, test_manager):
        """测试带预算的项目"""
        pass
    
    def test_project_validation(self, Project, test_manager):
        """测试项目数据验证"""
        pass
    
    def test_project_status_initialization(self, Project, test_manager):
        """测试项目状态初始化"""
        pass
```

### TestMilestoneManagement - 里程碑管理测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestMilestoneManagement:
    """里程碑管理测试"""
    
    def test_create_milestone(self, Milestone, test_project):
        """测试创建里程碑"""
        pass
    
    def test_milestone_with_deadline(self, Milestone, test_project):
        """测试带截止日期的里程碑"""
        pass
    
    def test_milestone_ordering(self, Milestone, test_project):
        """测试里程碑排序"""
        pass
    
    def test_milestone_completion(self, Milestone, test_project):
        """测试里程碑完成"""
        pass
    
    def test_milestone_progress_calculation(self, Milestone, Task, test_project):
        """测试里程碑进度计算"""
        pass
    
    def test_update_milestone(self, Milestone, test_project):
        """测试更新里程碑"""
        pass
    
    def test_delete_milestone(self, Milestone, Task, test_project):
        """测试删除里程碑"""
        pass
```

### TestTaskBreakdown - 任务分解测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTaskBreakdown:
    """任务分解测试"""
    
    def test_create_task(self, Task, Milestone, test_project):
        """测试创建任务"""
        pass
    
    def test_create_subtask(self, Task, test_project):
        """测试创建子任务"""
        pass
    
    def test_task_hierarchy(self, Task, test_project):
        """测试任务层次结构"""
        pass
    
    def test_task_with_estimates(self, Task, test_project):
        """测试带工时估算的任务"""
        pass
    
    def test_task_priority(self, Task, test_project):
        """测试任务优先级"""
        pass
    
    def test_task_tags(self, Task, test_project):
        """测试任务标签"""
        pass
```

### TestTaskAssignment - 任务分配测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTaskAssignment:
    """任务分配测试"""
    
    def test_assign_task_to_user(self, Task, TaskAssignment, test_manager, test_team_members):
        """测试分配任务给用户"""
        pass
    
    def test_assign_multiple_users(self, Task, TaskAssignment, test_team_members):
        """测试分配多个用户"""
        pass
    
    def test_reassign_task(self, Task, TaskAssignment, test_team_members):
        """测试重新分配任务"""
        pass
    
    def test_unassign_task(self, Task, TaskAssignment):
        """测试取消分配"""
        pass
    
    def test_workload_distribution(self, Task, TaskAssignment, test_team_members):
        """测试工作量分配"""
        pass
    
    def test_assignment_notification(self, Task, TaskAssignment, User):
        """测试分配通知"""
        pass
```

### TestDependencyTracking - 依赖跟踪测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
@requires_capabilities((CapabilityCategory.CTE, CTECapability.RECURSIVE_CTE))
class TestDependencyTracking:
    """任务依赖跟踪测试"""
    
    def test_create_dependency(self, Task, TaskDependency, test_project):
        """测试创建任务依赖"""
        pass
    
    def test_finish_to_start_dependency(self, Task, TaskDependency):
        """测试完成-开始依赖"""
        pass
    
    def test_start_to_start_dependency(self, Task, TaskDependency):
        """测试开始-开始依赖"""
        pass
    
    def test_circular_dependency_prevention(self, Task, TaskDependency):
        """测试防止循环依赖"""
        pass
    
    def test_dependency_chain(self, Task, TaskDependency):
        """测试依赖链"""
        pass
    
    def test_critical_path(self, Task, TaskDependency, test_project):
        """测试关键路径"""
        pass
    
    def test_blocked_tasks(self, Task, TaskDependency):
        """测试被阻塞的任务"""
        pass
```

### TestProjectTeam - 项目团队测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestProjectTeam:
    """项目团队测试"""
    
    def test_add_team_member(self, Project, ProjectTeam, User, test_project):
        """测试添加团队成员"""
        pass
    
    def test_remove_team_member(self, ProjectTeam, test_project):
        """测试移除团队成员"""
        pass
    
    def test_team_roles(self, ProjectTeam, test_project, test_team_members):
        """测试团队角色"""
        pass
    
    def test_team_capacity(self, ProjectTeam, User, test_project):
        """测试团队容量"""
        pass
    
    def test_team_member_list(self, ProjectTeam, test_project):
        """测试团队成员列表"""
        pass
```

### TestGanttChartData - 甘特图数据测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestGanttChartData:
    """甘特图数据生成测试"""
    
    def test_generate_gantt_data(self, Project, Milestone, Task, test_project):
        """测试生成甘特图数据"""
        pass
    
    def test_timeline_visualization(self, ProjectTimeline, test_project):
        """测试时间线可视化数据"""
        pass
    
    def test_task_bars(self, Task, test_project):
        """测试任务条数据"""
        pass
    
    def test_dependency_links(self, Task, TaskDependency, test_project):
        """测试依赖连接线数据"""
        pass
    
    def test_milestone_markers(self, Milestone, test_project):
        """测试里程碑标记"""
        pass
    
    def test_progress_overlay(self, Task, test_project):
        """测试进度覆盖显示"""
        pass
```

### TestProjectProgress - 项目进度测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestProjectProgress:
    """项目进度测试"""
    
    def test_calculate_project_progress(self, Project, Task, test_project):
        """测试计算项目进度"""
        pass
    
    def test_milestone_progress(self, Milestone, Task):
        """测试里程碑进度"""
        pass
    
    def test_task_completion_rate(self, Task, test_project):
        """测试任务完成率"""
        pass
    
    def test_progress_by_team_member(self, Task, TaskAssignment, User):
        """测试按团队成员统计进度"""
        pass
    
    def test_burndown_chart_data(self, Task, test_project):
        """测试燃尽图数据"""
        pass
```

### TestTaskStatus - 任务状态测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestTaskStatus:
    """任务状态测试"""
    
    def test_task_status_transitions(self, Task, test_project):
        """测试任务状态转换"""
        pass
    
    def test_start_task(self, Task, test_project):
        """测试开始任务"""
        pass
    
    def test_complete_task(self, Task, test_project):
        """测试完成任务"""
        pass
    
    def test_reopen_task(self, Task, test_project):
        """测试重新打开任务"""
        pass
    
    def test_block_task(self, Task, test_project):
        """测试阻塞任务"""
        pass
    
    def test_invalid_status_transition(self, Task):
        """测试无效状态转换"""
        pass
```

### TestDeadlineManagement - 截止日期管理测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestDeadlineManagement:
    """截止日期管理测试"""
    
    def test_set_task_deadline(self, Task, test_project):
        """测试设置任务截止日期"""
        pass
    
    def test_overdue_tasks(self, Task, test_project):
        """测试逾期任务"""
        pass
    
    def test_upcoming_deadlines(self, Task, test_project):
        """测试即将到期任务"""
        pass
    
    def test_deadline_notifications(self, Task, User):
        """测试截止日期通知"""
        pass
    
    def test_extend_deadline(self, Task, test_project):
        """测试延期"""
        pass
```

### TestProjectStatistics - 项目统计测试

```python
@pytest.mark.realworld
@pytest.mark.scenario_project
class TestProjectStatistics:
    """项目统计测试"""
    
    def test_project_summary(self, Project, Task, Milestone):
        """测试项目摘要统计"""
        pass
    
    def test_task_distribution(self, Task, TaskAssignment):
        """测试任务分布"""
        pass
    
    def test_resource_utilization(self, TaskAssignment, User):
        """测试资源利用率"""
        pass
    
    def test_velocity_calculation(self, Task, test_project):
        """测试速度计算"""
        pass
    
    def test_project_health_metrics(self, Project, Task, test_project):
        """测试项目健康度指标"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **项目创建**
   - 项目创建
   - 起止日期
   - 预算设置
   - 数据验证
   - 状态初始化

2. **里程碑管理**
   - 里程碑创建
   - 截止日期
   - 里程碑排序
   - 完成标记
   - 进度计算
   - 里程碑更新/删除

3. **任务分解**
   - 任务创建
   - 子任务
   - 任务层次
   - 工时估算
   - 优先级
   - 任务标签

4. **任务分配**
   - 单人分配
   - 多人分配
   - 重新分配
   - 取消分配
   - 工作量分配
   - 分配通知

5. **依赖跟踪**
   - 创建依赖
   - FS/SS依赖类型
   - 循环依赖防止
   - 依赖链
   - 关键路径
   - 阻塞任务

6. **项目团队**
   - 成员添加/移除
   - 团队角色
   - 团队容量
   - 成员列表

7. **甘特图数据**
   - 数据生成
   - 时间线可视化
   - 任务条
   - 依赖连接
   - 里程碑标记
   - 进度显示

8. **项目进度**
   - 项目进度计算
   - 里程碑进度
   - 任务完成率
   - 按成员统计
   - 燃尽图数据

9. **任务状态**
   - 状态转换
   - 开始/完成任务
   - 重新打开
   - 阻塞任务
   - 转换验证

10. **截止日期**
    - 设置截止日期
    - 逾期任务
    - 即将到期
    - 截止通知
    - 延期处理

11. **项目统计**
    - 项目摘要
    - 任务分布
    - 资源利用率
    - 速度计算
    - 健康度指标

### 所需能力（Capabilities）

- **递归CTE**：任务依赖链、关键路径查询
- **关系加载**：项目->里程碑->任务的复杂关系
- **聚合函数**：进度计算、统计分析
- **查询构建**：复杂的任务查询、报表生成

### 测试数据规模

- 项目：3-10 个项目
- 里程碑：每个项目 5-15 个里程碑
- 任务：每个里程碑 5-20 个任务
- 团队成员：5-20 个成员
- 任务依赖：20-30% 的任务有依赖关系

### 性能预期

- 项目创建：< 100ms
- 任务创建：< 50ms
- 任务分配：< 50ms
- 依赖关系创建：< 50ms
- 关键路径计算：< 500ms（100个任务）
- 甘特图数据生成：< 1s（100个任务）
- 项目进度计算：< 200ms
- 燃尽图数据：< 300ms
