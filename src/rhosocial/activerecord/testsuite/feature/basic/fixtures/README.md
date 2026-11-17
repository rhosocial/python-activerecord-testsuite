# Basic 夹具目录：重设计计划

- 日期：2026-11-16
- 状态：**待审定**（审定前不写实现；按 §10 分阶段）
- 范围：`src/rhosocial/activerecord/testsuite/feature/basic/fixtures/` 及其服务的
  `basic/*` 测试目录
- 依据：
  - `python-activerecord-testsuite/.claude/plan/2026-11-15/plugin-redesign.md`（铁律 R1–R9）
  - `python-activerecord/.claude/add_new_testcase.md`（新增用例规范）
  - `python-activerecord/.claude/plan/2026-11-16/README.md`（索引与审定清单）
  - `python-activerecord/.claude/plan/2026-11-16/complex-value-types.md`（三层通盘、24 键）
  - `python-activerecord/.claude/plan/2026-11-16/minimal-definition.md`（零注记建表）
  - `python-activerecord/.claude/plan/2026-11-16/backends-plan.md`（十个后端逐仓计划）
  - `python-activerecord/.claude/plan/2026-11-16/ddl-source-capabilities.md`（能力声明）
  - `python-activerecord/.claude/plan/2026-11-16/type-capacity-and-precision.md`
    （内容类型容量、毫秒默认与微秒开关）

---

## 0. 一句话

**模型即定义。** 一张表由一个模型类的注解声明，DDL 由
`base/derivation.py` 从注解派生，不再有手写的 `Definition` 列清单；每个声明集合
配一份同目录的 DDL/DML 操作；夹具按「组」组织，每组 = 一个测试目录 = 一个库。

### 0.1 适用范围与所有权

本目录是 **`basic` 范围内唯一的夹具定义处**，两个方向相反的规则：

- **向内收**：`basic/` 下所有测试目录（`crud`、`types*`、`nopk`、`readonly`、
  `validation`、`connection`、`worker`、`transaction`、`bulk_crud`）**不再私自定义
  夹具** —— 模型、适配器、DDL/DML 操作一律取自本目录。测试目录里只保留
  `pytest` 夹具函数与断言；`conftest.py` 只做「挑表 → 建表 → 交给用例」。
- **向外借**：**其他 feature 允许使用本目录的夹具**。`feature/cli` 已改用
  `user_models.BASIC_FIXTURES` / `BASIC_TABLES` 派生它借用的三张表；
  `feature/query/conftest.py` 目前仍从 `fixtures.models` 导入
  `OrderItem` / `AsyncOrderItem`——这是**临时遗留**，本轮不动，但在夹具
  彻底重新划分时 query 也必须改用它自己的夹具或新的 basic 分组公开名，
  不得再直连 `fixtures.models` 的内部类。这条是单向的：本目录**不反向依赖**
  任何 feature，也不从别的 feature 借模型。

由此产生两条硬约束：

1. 本目录的公开名字（模型类名、表来源清单）带有**跨 feature 契约**属性。
   改名、删除、改变语义必须同批更新 `feature/query`、`feature/cli` 的
   `conftest.py`，并在提交说明里点名影响面。
2. `BASIC_DEFINITIONS`（`{表名: Definition}`）已随 P1 消失，替换为
   `BASIC_TABLES`（模型类元组，建表来源，见 `user_models.py`）。
   `cli/conftest.py` 已改用 `BASIC_FIXTURES` 派生这三张表。

---

## 1. 现状盘点（本目录）

当前 `models.py` 有 **66 个类**（33 组同步/异步对）＋ **17 个手写 `Definition`**，
`models_py310/311/312.py` 是其中约 35 个类的手抄副本（各 667–693 行）。

| 现状 | 数量 | 问题 |
|---|---|---|
| 模型类 | 66 | 字段只写 Python 类型，无 DDL 声明 |
| `Definition` 类 | 17 | 把同一张表的列清单再手写一遍（`UserDefinition.columns()` vs `User`） |
| 版本副本 | 3 份 | 手抄，必然漂移（`User.email` 在 `models.py` 是 `EmailStr`，在 3.10+ 是 `str`） |
| 共用同表名的模型 | 6 张表 | `users` 被 `User`/`MappedUser` 共用，`order_items` 被 `OrderItem`/`MappedOrderItem` 共用，`product` 被 4 个模型共用 |
| 有 DDL 声明的字段 | ≈2 | 只有 `DefaultTimestampMixin` 的 `created_at`/`updated_at` |
| `basic/` 下私有模型 | 4 处 / ≈40 类 | 见 §3.1，模型定义散在测试目录里 |

实跑 `build_create_table_statement(User, SQLiteDialect())` 的直接结果：
`ValueError: users.id declares no SQL type` —— 66 个类里没有一个能派生自己的表。

### 1.1 已核实的机制事实（决定设计边界）

| # | 事实 | 位置 |
|---|---|---|
| F1 | 注解 → DDL 已经可用：`UseSqlType` / `UseColumnAttributes(IdentityAttribute())` / `UseConstraint` / `UseIndex` / `UseComment` / `UseColumnType` / `UseColumn` / `UseAdapter`，派生入口 `build_create_table_statement(source, dialect)` | `python-activerecord/base/ddl.py`、`base/derivation.py` |
| F2 | 声明期不需要方言：`PromptRow` 同一份注解在 sqlite / mysql / postgres 分别派生出 `INTEGER PRIMARY KEY AUTOINCREMENT` / `INT PRIMARY KEY AUTO_INCREMENT` / `SERIAL` | 实跑，见 §1.2 |
| F3 | **DDL 存储类型没有推断**：`column_data_type()` 只返回显式 `UseSqlType`，Python 类型不参与 | `base/ddl.py:892` |
| F4 | **DML 列类有推断**：无 `UseColumnType` 时，方言按 Python 类型答 `suggested_column_types()` | `base/field_proxy.py:249`、`impl/sqlite/mixins/column_type.py` |
| F5 | 列类与存储类型**刻意互不读取** | `backend/expression/column_types.py:26` |
| F6 | 派生会按 `Optional` 自动加 `NOT NULL`；显式 `UseConstraint(ColumnNullableConstraint)` 可以推翻 | `base/ddl.py:966` |
| F7 | `TextType()` **没有长度参数**；`TimestampType(precision=...)` 各家行为差异极大 | 见 §1.3 |
| F8 | 能力探针的答案依赖服务器版本，`introspect_and_adapt()` 之前可能全部为 False | `impl/oracle/mixins/features.py:201` |
| F9 | 能力回答有两条**互不重叠**的通道：零参布尔方法 与 `supports_data_types()` 字典；`Requirement` 只接前者 | `pytest_plugin/requirements.py:74`、实跑 §1.3 |
| F10 | `resolve()` 已支持「新版模块只覆盖它定义的名字」，未定义的回落到 `models.py` | `fixtures/__init__.py` |
| F11 | **数据库赋值是推导出来的，不是声明出来的**：单列整数主键写成 `Optional[int]`（可省略）且 `pk_auto_generated()` 为默认 True，就足以让写路径不要求主键、让 DDL 派生出后端自己的生成机制。实测：`Optional[int]` 与显式 `IdentityAttribute()` 在同一方言上派生出的 DDL 逐字相同 | `python-activerecord/base/derivation.py:264–296`、`field/integer_pk.py:5–18` |
| F12 | **`suggested_column_types()` 是成文契约**：`FRAMEWORK_PYTHON_TYPES` 的 **24 键每键必答**，漏键 = 硬失败。2026-11-17 已补齐：六族有 core 列类、`timedelta` 答 `IntervalColumn`；十方言全答满，唯一 `None` 是 Firebird 的 `dict` + 四个容器（无 JSON 读取函数、无原生数组），是明确拒绝而非漏答 | `protocols/query/column_type.py:31`、`base/field_proxy.py:266`、`base/framework_types.py` |
| F13 | 存储类型侧已有**「渲染或替代」二选一**纪律：每个类型概念必须被 `format_data_type_<name>` 渲染，或在 `substitute_data_types()` 里给出替代类，两者互斥；沉默 = `TypeError` | `protocols/query/data_type.py:85` |

### 1.2 注解 → 三方言（实测输出）

```python
class PromptRow(ActiveRecord):
    @classmethod
    def table_name(cls): return "prompt_rows"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    label: Annotated[str, UseSqlType(VarCharType(length=64)),
                     UseConstraint(ColumnUniqueConstraint)]
    amount: Annotated[Optional[Decimal], UseSqlType(DecimalType(precision=10, scale=2))] = None
    seen_at: Annotated[Optional[object], UseSqlType(TimestampType(precision=6))] = None
```

```
sqlite    CREATE TABLE "prompt_rows" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
          "label" TEXT UNIQUE NOT NULL, "amount" NUMERIC, "seen_at" NUMERIC)
mysql     CREATE TABLE `prompt_rows` (`id` INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
          `label` VARCHAR(64) UNIQUE NOT NULL, `amount` DECIMAL(10, 2), `seen_at` TIMESTAMP(6))
postgres  CREATE TABLE "prompt_rows" (`id` SERIAL NOT NULL,
          `label` VARCHAR(64) UNIQUE NOT NULL, `amount` DECIMAL(10,2), `seen_at` TIMESTAMP(6))
```

同一份模型在 sqlite 上还跑通了 `create_table → save → find_one → drop_table`
（`Decimal` 往返无损）。

### 1.3 类型渲染矩阵（实测，决定 §4–§6 的取舍）

对每个可用方言调 `dialect.format_data_type(...)`，不连库：

| 类型 | sqlite | mysql/mariadb | postgres | sqlserver | oracle | clickhouse | firebird |
|---|---|---|---|---|---|---|---|
| `TextType()` | TEXT | TEXT | TEXT | NVARCHAR(MAX) | **CLOB** | String | BLOB SUB_TYPE TEXT |
| `VarCharType(64)` | TEXT | VARCHAR(64) | VARCHAR(64) | VARCHAR(64) | VARCHAR2(64) | String | VARCHAR(64) |
| `TimestampType()` | NUMERIC | TIMESTAMP | TIMESTAMP | DATETIME2 | TIMESTAMP | **DateTime（秒）** | TIMESTAMP |
| `TimestampType(6)` | NUMERIC | TIMESTAMP(6) | TIMESTAMP(6) | DATETIME2(6) | TIMESTAMP(6) | DateTime64(6) | **硬报错** |
| `JsonType()` | TEXT | JSON | JSON | NVARCHAR(MAX) | **VARCHAR2(4000)** | String | 硬报错（建议 TextType） |
| `BlobType()` | BLOB | BLOB | BYTEA | VARBINARY(MAX) | BLOB | String | BLOB |
| `UUIDType()` | 硬报错 | 硬报错 | UUID | 硬报错 | 硬报错 | UUID | CHAR(16) OCTETS |

值得记住的三个后果：

1. **`TextType()` 今天无法表达容量**（F7 没有 `length`），只能表达「这一类」。
   裁决见 `type-capacity-and-precision.md`：五个内容类型（`TextType` / `BlobType` /
   `JsonType` / `JsonBType` / `XmlType`）补 `length`，语义是「至少装下 N 个字符」，
   方言**向上取档**、按最坏 4 字节/字符换算（Oracle 的 4 000 是字节、SQL Server 的
   4 000 是字符）。没有它，长内容这条轴在共享套件里只能靠「后端名 + 后端类型」表达。
2. **Oracle 的 `JsonType()` 是 `VARCHAR2(4000)`** —— 4 000 字节上限，长 JSON 装不下；
   这不是「不支持 json」，是容量问题，必须由夹具按容量选内容。
3. **`TimestampType(6)` 在 Firebird 上是硬报错**（它存储固定 1/10000 秒，拒绝声明一个
   服务器无法兑现的精度）。裁决：**默认毫秒（`precision=3`）**，Firebird 接受
   precision ≤ 4 并渲染 `TIMESTAMP`；微秒是补充能力
   （`supports_microsecond_timestamp()`，Firebird 答 False），不进共享默认值。

MySQL 侧还有两个实测行为（`clic_ts_precision.py`，MySQL 5.7.44）：

```
TIMESTAMP    10:00:00.123456 -> 10:00:00       （截断）
TIMESTAMP    10:00:00.600000 -> 10:00:01       （**进位到下一秒**）
TIMESTAMP(6) 10:00:00.123456 -> 10:00:00.123456
```

进位比截断更糟：写进去的 `updated_at` 会比真实时间**晚**，甚至可能超过 `now()`。

---

## 2. 设计原则

在 R1–R9 之上，本目录新增四条：

### P1 模型即定义，`Definition` 消失

一张表只有一个声明来源：模型类。L2 从它派生：

```python
for source in TABLE_SOURCES:
    backend.execute(*build_create_table_statement(source, backend.dialect).to_sql(), options=DDL)
```

`Definition`、`auto_pk()`、`fixture_types.py` 的 `short_text`/`long_text`/`timestamp_type`
一并删除。同一张表被多个模型声明时，**只指定一个来源**建表，其余模型只绑定不派生。

### P2 默认 / 注记 两变体对照

| 变体 | 声明内容 | 用来回答 |
|---|---|---|
| **bare（完全默认）** | **模型自己写的字段只有 Python 类型注解，没有任何 `Annotated` 标记** | 「什么都不说时，框架给什么？」 |
| **annotated（完全注记）** | 同一批 Python 类型 + 覆盖全部注记轴（类型/长度/精度、约束、索引、注释） | 「注记改变了什么？」 |

**identity 不属于注记轴**。数据库赋值整数主键由 `Optional[int]` + `pk_auto_generated()`
默认推导（F11），两变体一致；`IdentityAttribute` 是机制专属的 DDL 提示，不写进共享夹具。
自增行为用 `supports_database_assigned_integer_column()` 在行为层单独验证，DDL 机制留给各后端。

三点必须说清楚：

- **bare 是字面意义的「光秃秃」**，不是「少写几个标记」。它对应产品承诺
  「写个类就能建表」（`minimal-definition.md`），也对应本项目 README 里要写的
  「最简定义」。因此 bare 组是**该承诺的验收夹具**，不是可选装饰。
- **bare 只差 DDL 侧的推断**（F3）：DML 侧早已按 Python 类型选列类，而且是**成文契约**
  —— `suggested_column_types()` 的 18 个键每键必答，漏键硬失败（F12，实测 10 个方言
  全部答满）。缺的是同一件事的存储类型版本：`column_data_type()` 只读显式 `UseSqlType`。
  所以 bare 变体随 core 的 `minimal-definition` 一起启用；推断表已落地为
  `suggested_data_types()`（24 键、每键必答、无 `None`），与列类表同纪律。
- **「零注解」只约束模型自己写的字段**。从 mixin 继承的声明（`DefaultTimestampMixin`
  给的 `created_at`/`updated_at`）照旧 —— 那是框架给的，不是用户写的；它们的精度随
  mixin 的默认值走（毫秒，见 §4）。同理，主键约定若最终由 mixin 提供，也算框架声明。

注记分两类，这决定了它们是**两张表**还是**一张表**：

- **改变存储的注记**（存储类型/长度/精度、identity、约束、索引、注释）→
  两张表，对照的是「表定义差异」。
- **不改变存储的注记**（`UseColumn` 改列名、`UseAdapter` 改值适配、pydantic 校验）
  → **共用一张表**，对照的是「同一存储下的行为差异」。

### P3 版本轴：3.8 为基线，只按「注解语法 / 注解求值语义」分界

支持范围 **3.8–3.15**（`requires-python = ">=3.8"`，core CI 覆盖 3.8–3.13 + 3.14 + 3.15
+ free-threaded 3.13t/3.14t）。跨版本要验证的是「同一批注记在不同拼写下行为一致」，
不是「把 35 个类抄 N 遍」。利用 F10：矩阵只在基线写一次；每个版本文件只定义该版本
**独有的语法**探针，未定义的名字回落到基线。

现状 `VERSION_MODULES = (("312", (3, 12)), ("311", (3, 11)), ("310", (3, 10)))` ——
3.8/3.9 用基线，3.10+ 逐级覆盖。按「注解 → DDL」这条轴逐一核对 3.9–3.15：

| 版本 | 影响模型声明的变化 | 是否单独建文件 | 理由 |
|---|---|---|---|
| 3.8 | 基线：`typing.List/Dict/Optional/Union` | `models.py` | 语法下界 |
| 3.9 | PEP 585：`list[str]`、`dict[str, int]` 运行期可下标 | **新增 `models_py39.py`** | 3.8 上直接 `TypeError` 的唯一语法分界；验证内建泛型注解派生的 DDL 与基线逐字相同 |
| 3.10 | PEP 604：`X \| Y` | `models_py310.py`（已有） | 注解语法的第二次分界 |
| 3.11 | `typing.Self`、`LiteralString`、PEP 646/655 | `models_py311.py`（已有） | `Self` 只出现在方法返回注解（不进列）；`LiteralString` 进列，验证它仍被当作 `str` |
| 3.12 | `typing.override`（PEP 698；3.11 无此名字） | `models_py312.py` | 用 `@override` 修饰 `table_name()`；PEP 695 `type` 别名因与仓库 ruff 目标版本冲突不采用 |
| 3.13 | PEP 696 类型参数默认值、`typing.ReadOnly`、`TypeIs` | **不建文件** | 三者都作用于 TypedDict / 泛型参数，不改变列声明；`resolve()` 落到 3.12 文件 |
| 3.14 | **PEP 649/749 惰性注解求值**（`__annotate__`） | **新增 `models_py314.py`** | 唯一**改变语义**而非语法的变化：注解不再在类创建时求值。框架若依赖立即求值，会在 3.14 上失效 |
| 3.15 | 无影响本轴的已知变更 | **不建文件** | 落到 3.14 文件；一旦出现注解语义变更再加 |

`VERSION_MODULES` 按新方案改为
`(("314", (3, 14)), ("312", (3, 12)), ("311", (3, 11)), ("310", (3, 10)), ("39", (3, 9)))`。

`models_py314.py` 探针要点（PEP 649）—— 三条都是**风险点，不是已核实的结论**，
实施阶段 6 之前先在 3.8 与 3.14 上各跑一遍确认现状：

1. `Annotated[..., UseSqlType(...)]` 的元数据在惰性求值下仍可读出；
2. 指向**其后才定义**的名字的前向引用仍能派生（失败会推迟到读取时）；
3. 读 `cls.__annotations__` 与读 `__annotate__` 得到同一份注记，且其中某个名字解析失败
   时能指名到列，而不是整张表崩掉。

探针的取用方式：**走 `resolve()`**。版本文件只定义自己的 `TypingProbeN`，其余名字由
`resolve()` 逐级回落到基线；因此探针名本身天然按解释器版本门控 —— 当前解释器能导入的
最高版本文件定义它，更低版本的探针名则回落到基线（基线没有这个名字）而不可用。
DB-free 契约测试断言「当前解释器上 `resolve()` 取到的探针属于正确的版本文件」，
避免回落链写错后静默测了别的版本。3.13 / 3.15 不建文件，分别回落到 3.12 / 3.14。

### P4 同步异步同源

字段声明放进一个普通 mixin（既有做法，`PydanticValidatedFieldsMixin` 就是这样），
两个孪生类只声明 `table_name()` / `primary_key()`：

```python
class UserFields:                      # 唯一的字段声明
    id: Annotated[Optional[int], SQL_INT_PK, IDENTITY] = None
    username: Annotated[str, SQL_TEXT_255]

class User(UserFields, IntegerPKMixin, ActiveRecord): ...
class AsyncUser(UserFields, IntegerPKMixin, AsyncActiveRecord): ...
```

再加一条 DB-free 契约：**同表的同步/异步孪生模型派生出的 CREATE/DROP 必须逐字相同**，
抓住任何一处单边漂移。bare 组同样适用；裸模型孪生派生结果一致，也顺带验证了推断
不依赖 sync/async 类层次。

---

## 3. 夹具组划分

组 = 一个测试目录 = 一个库 = 一个声明集合 = 一套操作。
`Mapped*` / `ColumnMapping*` / `TypeAdapter*` 不再独立成组，按 P2 归入各自组的
**annotated 变体**（它们不改变存储，所以与 bare 共用一张表）。

| 组（目录） | 表 | bare | annotated | 注解是否改存储 | 能力前提 |
|---|---|---|---|---|---|
| `crud/` | `users` | `User`（零注记） | `UserAnnotated`（唯一、索引） | 是 → 两表 | 数据库赋值整数列 |
| `crud/` | `users`（映射对照） | `User` | `MappedUser`（`UseColumn`） | 否 → 同表 | — |
| `crud_composite_pk/` | `order_items`、`store_inventory`、`orders` | `OrderItem`、`StoreInventory`（零注记，复合键天然不是 identity） | `MappedOrderItem`（`UseColumn` + 复合 PK） | 否 → 同表 | 复合 PK |
| `types/`（新） | `typed_users`、`typed_users_annotated` | ✓ | ✓ | 是 → 两表 | 标量类型概念 |
| `types/`（新，补充） | `microsecond_rows` | —（只有 2 列，不设 bare） | ✓ | — | `supports_microsecond_timestamp`（2026-11-18 已落地） |
| `types_complex/`（新） | `complex_rows`、`complex_rows_annotated` | ✓（含 `MacAddress` / `Point` 等后端建议表里有的业务类；`Vector`/`Range` 除外） | ✓ | 是 → 两表 | 各概念（json/array/uuid/blob/interval/enum）+ 业务类（geometry / mac） |
| `types_long_content/`（新） | `long_rows` | **无** | ✓ | — | text / blob / json / xml 的概念与容量 |
| `fields/` | 复用 `users` | `User` | `ColumnMappingModel`（`UseColumn`+`UseAdapter`）、派生字段 | 否 → 同表 | — |
| `type_adapter/` | `adapter_rows` | `AdapterRow` | `AdapterRowAnnotated`（`UseAdapter`+`UseColumnType`） | 否 → 同表 | — |
| `validation/` | `validated_rows` | —（无语义） | `ValidatedRow`（pydantic 校验） | 否 → 同表 | — |
| `bulk_crud/` | `bulk_users` | `BulkUser` | — | — | — |
| `expressions/`（新） | **无**（复用上述表） | — | — | — | 列类（B 层 24 键） |

结构组（`nopk/`、`readonly/`、`transaction/`、`worker/`、`connection/`）**不按
bare/annotated 重划**：它们的对照点是行为声明（无主键、只读、连接生命周期），
不是类型覆盖，硬套两变体只会得到一批没人读的孪生类。但按 §0.1，**它们的模型定义
同样收归本目录**（§3.1）—— 它们大多是 `users` / `test_users` 的投影，不需要自己的 DDL。

**拆分判据**（沿用 R4）：声明集合不同 / 能力前提不同 / 失败后果不同。
三个类型组之所以分开，是**能力前提不同**：标量组任何后端都能用普通列承载；
复杂组依赖具体类型概念；长内容组依赖容量，失败后果是「装不下」而不是「不支持类型」。

### 3.1 basic 范围内的私有夹具：全部收归本目录

按 §0.1 清点，`basic/` 下还有四处在测试目录里私自定义模型：

| 现状位置 | 私有声明 | 绑定的表 | 迁移后文件 | 自带 DDL |
|---|---|---|---|---|
| `connection/fixtures.py` | `TestUser`/`AsyncTestUser` | `test_users` | `connection_models.py` | 否 —— 建表一直靠 `models.py` 里的 `TestUserDefinition`，模型与定义分居两处正是要修的地方 |
| `nopk/test_keyless_models{,_async}.py` | 各 4 个（`KeylessUser`、`KeylessReadOnlyUser`、`ReadOnlyWithKeyUser`、`NormalUser`） | `users` | `user_models.py` | 否（投影） |
| `readonly/test_readonly_models{,_async}.py` | 各 5 个（`ReadOnlyUser`、`WritableUser`、`OptedOutUser`、`ImplementsButWritable`、`ReadOnlyView`） | `users` | `user_models.py` | 否（投影） |
| `validation/test_pydantic_native_validation{,_async}.py` | 各 15 对同步/异步模型（30 个类）+ `RecordStatus`、`AddressPayload`；两个文件的模型块（前 400 行）除文件头注释外**逐字相同** | 无（DB-free 契约） | `pydantic_native_models.py` | 否 |

要点：

- **`user_models.py` 收 `users` 表的全部声明**：`crud`/`fields` 的读写模型、
  `nopk` 的无主键投影、`readonly` 的只读投影。它们的**声明集合不同**（§3 的拆分判据），
  所以仍是不同的测试组；但**一张表只在一个文件里声明**。
- **`pydantic_native_models.py` 是纯 DB-free 契约**：不需要 DDL；顺带用 P4 的 mixin
  做法消掉两个文件里那 400 行重复。
- **`connection` 组**过去把「模型」和「建表定义」拆在两处；迁移后由 `TestUser`
  自己的注解派生，两者合一。
- `worker/`、`transaction/` 目前没有私有模型，迁移只涉及 `conftest.py` 里挑表的方式。
- 结构组的模型迁移**不改变测试内容**，只是把定义挪进来并接上派生 DDL。

---

## 4. 类型组一：`types/`（简单/标量）

表 `typed_users` 与 `typed_users_annotated`，同一批 Python 类型（用户指定的名字：
两类 `typed_user` —— 一颗完全默认、一颗完全注记）。

| 列 | Python 类型 | annotated 追加（bare 只有 Python 类型） |
|---|---|---|
| `id` | `Optional[int]` | `+ UseSqlType(IntegerType())`（identity 由 F11 推导，两变体相同） |
| `flag` | `bool` | `+ BooleanType() + ColumnDefaultConstraint(False)` |
| `count` | `int` | `+ IntegerType() + UseComment` |
| `amount` | `Decimal` | `+ DecimalType(precision=12, scale=2)` |
| `ratio` | `float` | `+ FloatType()`（浮点宽度是后端话题，不进共享套件） |
| `label` | `str` | `+ VarCharType(64) + ColumnUniqueConstraint + UseIndex("ix_…")` |
| `born_on` | `date` | `+ DateType()` |
| `wakes_at` | `time` | `+ TimeType()` |
| `seen_at` | `datetime` | `+ TimestampType(precision=3)`（毫秒，见 §4.1） |
| `note` | `Optional[str]` | `+ TextType()` |

bare 变体整列只写 Python 类型，**框架推断出什么就是什么**——这正是这一组的价值：
它把 `minimal-definition.md` 里 D1–D4 四个默认值（`str` 长度、`int` 宽度、
整数主键由数据库赋值、`Decimal` 精度）钉成可执行断言。默认值若改，这组测试必须跟着改，
这正是我们要的灵敏度。推断表现在已经存在：`suggested_data_types()` 的 24 键表，
与列类表同纪律（每键必答、无 `None`），bare 已可建表。

`TinyIntType`/`SmallIntType`/`BigIntType` **不进共享套件**：整数宽度是后端话题，
写进来就违反 R1。

### 4.1 毫秒是默认，微秒是补充能力

`TimestampType(6)` 在 Firebird 上是硬报错（§1.3），而 MySQL 5.7 / ClickHouse 的
**秒级** `TIMESTAMP` / `DateTime` 会截断甚至进位（`.600000` → 下一秒）。两个极端的
共同答案是**毫秒**：

- `DefaultTimestampMixin` 的 `created_at`/`updated_at` 改成
  `TimestampType(precision=3)`；只在 SQLite 上无所谓，在 PG / Oracle / SQL Server 上
  无损，在 MySQL / ClickHouse 上真正保留毫秒。
- Firebird 迁就：它存固定 1/10000 秒，**兑现得了毫秒**，所以接受 precision ≤ 4 并渲染
  `TIMESTAMP`，只拒绝 > 4 —— 拒绝的理由是「服务器兑现不了」，毫秒不属于这一类。
- 微秒不进共享默认值，改为**补充能力**：`supports_microsecond_timestamp()` 由各方言
  显式回答（Firebird 答 False），不设继承默认值（与 `suggested_column_types()` 的
  「core 里的表是对一台 core 没见过的服务器的猜测」同一取向）。
- Firebird 自己的 1/10000 秒测试留在 `python-activerecord-firebird`，不进共享套件（R1）。

微秒夹具是**独立的 2 列表** `microsecond_rows`，不拉长 `typed_users`：
`id` + `precise_at`（`TimestampType(precision=6)`）。它的 `create_table` 操作在
§8.1 里要求 `supports_microsecond_timestamp`，答否则跳过并指名；这一组不设 bare。

## 5. 类型组二：`types_complex/`（复杂类型）

bare 变体的边界由**后端的答案**决定，而不是由「是不是内建类型」决定：字段只写 Python
类型，后端在建议表里答得出就能 bare —— 框架建模的类型（18 个常见类型 + 6 个复杂族）查
**主表**（该组用到的键必答），后端自有类型查**extras**；答 `None` 就是「这个类不足以定
存储，必须注记」。

因此本组的列分三类：**常见类型**（bare 与 annotated 都有）、**类本身能定存储的业务类**
（`MacAddress`、`Point`，bare 与 annotated 都有）、**参数属列属性的业务类与 XML**
（`Vector`、`Range`、`BitString`、XML，只有 annotated）：

| 列 | Python 类型 | bare | annotated |
|---|---|---|---|
| `id` | `Optional[int]` | ✓ | ✓（identity 两变体相同，见 F11） |
| `token` | `UUID` | ✓ | `+ UseIndex("ix_…")` |
| `payload` | `dict` | ✓ | `+ UseComment`（容量见下） |
| `tags` | `list` | ✓ | `+ ArrayType(element_type=VarCharType(32))` |
| `elapsed` | `timedelta` | ✓ | `+ IntervalType()` |
| `kind` | `Enum` | ✓ | `+ EnumType(...)` |
| `raw` | `bytes` | ✓ | `+ UseColumnType(BinaryColumn)`（显式钉死列类） |
| `nic` | `MacAddress`（core 业务类） | ✓（后端 extras 答得出时） | `+ UseAdapter(...)`（钉死适配器） |
| `location` | `Point`（core 业务类） | ✓（得到**通用** `GEOMETRY` 列） | `+ UseSqlType(<子类型/SRID>)` 精确列 |
| `heading` | `Vector`（core 业务类） | **不可 bare**：维度是列属性 | `+ UseSqlType(<vector(n)>)` |
| `markup` | `str` | **不可 bare**：无 Python 类型可推 | `+ XmlType() + UseColumnType(XMLColumn)` |

三组边界各有来由：

- `MacAddress` / `Point` 的存储**由类本身决定**（无参数 / 通用几何），所以 bare 成立；
  几何子类型与 SRID 是「更精确的声明」，不是「必须的声明」。
- `Vector` / `Range` / `BitString` 的尺寸/元素类型仍是**列属性**，类里没有
  （`Vector` 源码原话：「dimension is not constrained here: a column's DDL decides it」）。
  2026-11-17 后 core 已给它们列类、后端已给文本/JSON 载体，所以 bare **可以建表**；
  但要原生语义（维度、元素类型、位宽）仍须 `UseSqlType(...) + UseColumnType(...)`。
- `markup` 是 XML，没有对应 Python 类型，只有 annotated 变体。

两个硬约束来自 §1.3 的实测：

- **Oracle 的 `JsonType()` 只有 `VARCHAR2(4000)`**。`payload` 的内容必须按 4 000 字节
  设计，否则在 Oracle 上是「容量不足」而不是「不支持 json」。容量前提要进 §8 的操作登记，
  不能靠测试体去猜。
- `UUIDType()` / `XmlType()` / `IntervalType()` 在多个方言上是**硬报错**
  （SQLite、MySQL、SQL Server 各自缺 formatter）。这不是缺陷，是能力：方言明确拒绝
  语义不成立的类型，而不是静默降级。bare 组在缺少这些概念的方言上按 §8 的开关跳过。

还有一条**只有 bare 会踩到**的边界（2026-11-17 复核）：24 键表现在全答，
MySQL/MariaDB 的 `dict` 与 PostgreSQL 的 `timedelta` 已有列类与建议存储类型，
不再需要按方言跳过。唯一仍拒绝的是 **Firebird 的 `dict` + 四个容器**（无 JSON 读取
函数、无原生数组）；bare 组按**逐列**登记能力（§8.1 的 `Operation.column`），
只在 Firebird 跳过并指名这些列；annotated 组用
`UseSqlType(JsonType()) + UseColumnType(...)` 显式承担，不受该限制。

bare 组的测试断言**只做值往返（写入=读出）**，不断言列类：列类由方言推断（F4），
断它等于把后端实现钉进共享套件。annotated 组可以用 `UseColumnType` 钉死列类，
因此可以断言 `JSONColumn`/`XMLColumn` 才有的操作。

## 6. 类型组三：`types_long_content/`（长内容）

长内容是复杂类型的子集：内容超出任何后端 `VARCHAR` 上界，只能落在 TEXT/CLOB/BLOB。
**这一组只有 annotated 变体** —— bare 的 `str` 会被推断成 `VARCHAR(255)` 级别的列，
根本装不下 16 000 字符；硬做 bare 只能得到一个必然截断的测试。

| 列 | Python 类型 | annotated | 前提 |
|---|---|---|---|
| `id` | `Optional[int]` | —（identity 由 F11 推导） | 数据库赋值整数列 |
| `body` | `str`（16 000 字符） | `TextType(length=16000)` | `text` 概念 **+ 容量** |
| `raw` | `bytes`（16 000 字节） | `BlobType(length=16000)` | `blob` 概念 **+ 容量** |
| `document` | `dict`（≤3 500 字符的 UTF-8） | `JsonType()` | `json` 概念 + Oracle 的 4 000 字节上限 |
| `markup` | `str`（≤3 500 字符的 XML） | `XmlType()` | `xml` 概念 |

**`length` 是这一组的前提**（`type-capacity-and-precision.md`）：语义是「至少装下 N 个
字符」，方言向上取档 —— MySQL ≤65 535 → `TEXT`、≤16 MB → `MEDIUMTEXT`、否则 `LONGTEXT`；
Oracle `N×4 ≤ 4000` → `VARCHAR2`，否则 `CLOB`；SQL Server ≤4 000 → `NVARCHAR(n)`，否则
`NVARCHAR(MAX)`；Firebird `N×4 ≤ 32765` → `VARCHAR`，否则 `BLOB SUB_TYPE TEXT`；
PG / ClickHouse / SQLite / Snowflake / BigQuery 本身无上限，忽略。容量参数落地前，这一组
无法在共享层表达「要一个装得下 16 000 字符的列」，只能写字面后端类型名（违反 R1），
所以它排在阶段 2b 之后。

**16 000 的由来**：Oracle 的 `VARCHAR2` 上限 4 000 字节，MySQL 的 `TEXT` 上限
65 535 字节；16 000 字符在两端之间，对所有后端都「超出 VARCHAR」，且能装进 MySQL 的
`TEXT`。内容只用 BMP 字符（≤3 字节/字符 → ≤48 KB），避开 MySQL `TEXT` 的边界 ——
换成 4 字节字符就会超过 65 535 字节，那时必须声明更大的档位，而不是换后端类型名。

`document` / `markup` 暂不写 `length`：json / xml 的容量语义还要单独裁决（Oracle 的
`JsonType()` 今天固定渲染成 `VARCHAR2(4000)`，加上 `length` 就得决定它从哪一档开始落到
`CLOB`）。所以在裁决之前，先把内容压在 4 000 字节内，按「json / xml 概念可用」跳过。

**这一组测的是「选对了 LOB 类型且装得下」，不是 LOB 的容量上限与溢出路径。**
后者（> 64 KB，MySQL 需要 `LONGTEXT`、Firebird 需要分段 BLOB）要等 §3 的档位语义
在全部后端落地，属于 `type-capacity-and-precision.md` 的后续阶段，本轮不做。

## 7. 文件布局（受「夹具目录禁 `__init__.py`、模型与适配器必须同文件」约束）

`fixtures/` 已有 `__init__.py`（历史例外，保留），但**不再新建子目录**，一律平铺模块：

| 文件 | 职责 |
|---|---|
| `README.md` | 本文 |
| `annotations.py` | 版本无关的中立声明常量（`SQL_INT_PK = (UseSqlType(IntegerType()),)`：整数主键由 `Optional[int]` + 默认推导赋予，不含机制注记，不含模型） |
| `user_models.py` | `users` 表的全部声明：`crud`/`fields` 的 `UserFields` + `User`/`AsyncUser` + `UserAnnotated` + `MappedUser` + `ColumnMappingModel`；`nopk` 的 4 个无主键投影；`readonly` 的 5 个只读投影 |
| `type_rows_models.py` | 三个类型组：字段基类 + 模型 + 其适配器 |
| `composite_pk_models.py` | `crud_composite_pk` 组（`OrderItem`/`StoreInventory`/`Order`/`MappedOrderItem`） |
| `connection_models.py` | `connection` 组：`TestUser`/`AsyncTestUser`（`test_users`） |
| `pydantic_native_models.py` | `validation` 组的 DB-free 契约模型 |
| `operations.py` | 表登记（DDL/DML 操作 + 能力开关，§8）与执行函数 |
| `models.py` | 基线（3.8）聚合并 re-export 上述组，`resolve()` 的回落目标 |
| `models_py39.py` | `TypingProbe39`：PEP 585 内建泛型 |
| `models_py310.py` / `py311` / `py312` / `py314` | 各只含一个 `TypingProbeN`（§2 P3）；3.13 / 3.15 无文件，靠回落 |

`__init__.py` 的 `resolve()` 机制不变（逐级回落、只覆盖定义过的名字），只是
`VERSION_MODULES` 增加 `314` 与 `39` 两级。探针走同一条 `resolve()` 回落链，
只由「该名字是否在某版本文件中定义」决定命中，不另设入口。

---

## 8. DDL / DML 操作与能力开关

操作只**执行**，不判定、不跳过、不探测（R3）；断言留在测试里。

```python
# fixtures/operations.py
DDL = ExecutionOptions(stmt_type=StatementType.DDL)

def create_schema(backend, tables):   # 每张表一次，含 create_index_statements
def drop_schema(backend, tables):     # if_exists=False：表是本夹具自己建的
def seed(model, rows):                # DML：规范行 → 插入 → 返回实例列表
def reload(model, pk):                # DML：按主键读回
```

`drop_schema` 用 `if_exists=False`（`build_drop_table_statement` 的默认值）：
表由夹具自己建、自己删，`IF EXISTS` 这一层猜测随之消失，`supports_drop_if_exists`
不再需要。

### 8.1 临时能力元数据（本轮的替代方案）

core 还没有「定义自己声明需要什么」的接口（`ddl-source-capabilities.md`）。
在它落地之前，本目录用一层**临时元数据**登记：每张表有哪些操作，每个操作要求
哪些开关**必须开**或**必须关**。

```python
@dataclass(frozen=True)
class Operation:
    name: str                          # "create_table" / "insert" / "drop_table" / ...
    requires_on: Tuple[str, ...] = ()  # 必须答 True
    requires_off: Tuple[str, ...] = () # 必须答 False
    column: Optional[str] = None       # 只涉及某一列时点名（§5 的 bare 边界）

@dataclass(frozen=True)
class TableFixture:
    table: str
    source: Optional[type]             # 建表来源模型；投影为 None
    operations: Tuple[Operation, ...]
```

已落地为 `fixtures/operations.py`，另有 `operation_reason(dialect, operation)` /
`table_reason(dialect, fixture)` 产出跳过理由（`None` 表示可执行），
以及 `create_schema` / `drop_schema` / `seed` / `reload` 四个只执行不判定的函数。

一个开关名按固定顺序解析（F9 的两条通道 + 硬失败）：

1. 方言上的零参布尔方法 → 调用（沿用 `requirements.answer()` 的严格性）；
2. `supports_data_types()` 的键 → 取其布尔值；
3. 都没有 → `MissingRequirementError`，指名方言与开关名。

于是跳过理由能精确到「`types_complex.payload` 的 `insert` 需要 `json`，方言答否」，
而方言漏实现则是**失败**而不是跳过 —— R1 要求的形状。

这层是临时的：core 接口落地后应退化为薄壳或整体删除，测试体不动。

---

## 9. 能力前提与跳过

一条链：**表登记 → L2 求值 → 不满足则 skip 并指名**。

- **求值位置必须在 L2**，在 `database` 已 `introspect_and_adapt()` 之后（F8）：
  版本相关的探针在适配前一律答 False，在 collection 期求值会误跳。
  `Declaration.requires` 现在的文档写的是 "call time"，那时表已经建过了，
  类型不支持会先在 `schema` 里炸掉 —— 这一处要改到 L2。
- 每组登记自己的操作与开关（§8.1），大致形状：

  | 组 | 主要开关 |
  |---|---|
  | `types/` | `integer` / `varchar` / `text` / `decimal` / `date` / `time` / `datetime`，以及 `create_table` 的 `identity`（仅 annotated）；`microsecond_rows` 另需 `supports_microsecond_timestamp` |
  | `types_complex/` | 上述 + `json` / `array` / `uuid` / `blob` / `interval` / `enum` |
  | `types_long_content/` | `text` / `blob` / `json` / `xml`，加上 §5 的容量限制 |

- **「不支持」= 跳过并指名**；**「方言没实现这个开关」= 硬失败**。两者不能混。

---

## 10. 迁移步骤

| 阶段 | 内容 | 验收 |
|---|---|---|
| 0 | core 两处收口：`_resolve_type` 只捕能力异常；本目录落地 §8.1 的临时能力元数据 | **已完成**（2026-11-17） |
| 1 | `annotations.py` + `operations.py` + `user_models.py` + `connection_models.py` + `composite_pk_models.py`；五组 conftest 改为派生建表；`BASIC_DEFINITIONS` → `BASIC_TABLES`，`cli/conftest.py` 同步 | **已完成**（2026-11-17）：core 的 `basic/{crud,crud_composite_pk,connection,nopk,readonly}` 与 `cli` 全绿 |
| 2a | core `minimal-definition` P0（标量推断）落地：24 键、每键必答，与 `suggested_column_types()` 同一套纪律 | **已完成**（2026-11-17）：`suggested_data_types()` 24 键全答，bare 可建表 |
| 2b | core 容量与精度：五个内容类型加 `length`；`DefaultTimestampMixin` 改毫秒；Firebird 接受 precision ≤ 4；`supports_microsecond_timestamp()` 进协议并由各后端回答 | **已完成**（2026-11-18）：`microsecond_rows` 2 列夹具 + sync/async 往返用例落在 `types/` 组；Firebird 方言覆盖 `supports_microsecond_timestamp()` 答 False，按能力跳过并指名；precision ≤ 4 由 Firebird 方言接受，毫秒为共享默认 |
| 3 | `types/` 两变体 + `microsecond_rows`（bare 此时才可建表） | **已落地**（2026-11-18）：`types_models.py` + `types/` 组，sync/async 同源，SQLite 两变体真实往返通过；`microsecond_rows` 已在阶段 2b 落地 |
| 4 | `types_complex/` 两变体 | **已落地**（2026-11-18）：`types_complex_models.py` + `types_complex/` 组，逐列能力登记；SQLite 14 passed；`Vector/Range/BitString` 仅 annotated、用可移植载体 |
| 5 | `types_long_content/`（annotated only，依赖 2b 的 `length`） | **已落地**（2026-11-18）：`types_long_content_models.py` + 组；SQLite 上 XML 无法声明，4 个 DB 用例指名跳过，DB-free 断言照常执行 |
| 6 | `fields/`、`type_adapter/`、`validation/` 按 bare/annotated 重排；`pydantic_native_models.py` 消重复 | **已落地**（2026-11-18）：三组各建 bare/annotated 变体 + sync/async 孪生，共用一张表（UseColumn/UseAdapter/校验不改存储），DDL 等价；pydantic native 模型收归 `pydantic_native_models.py`，两份测试去掉重复声明块；SQLite 声明级断言通过 |
| 6b | 新增 `expressions/` 组（§12）：X1–X6；复用既有表，不新增 DDL | **已落地**（2026-11-18）：`expressions/` 组 = conftest + sync/async 配对测试，复用 `TypedUser`/`ComplexRow` 等既有模型，只取方言的建议列类与运算，不连库、不建表；X1 断言 `Model.c.<field>` 的类 == 该方言 `suggested_column_types()` 答案，X2 七族各一运算渲染 SQL，X3 负向运算不存在（JSON 无 `like`、XML 不可比较），X4 `UseColumn` 用列名，X5 同步/异步同源，X6 漏答失败、None 跳过并指名；本地 SQLite 双半通过 |
| 7 | 版本文件只留探针：新增 `models_py39.py` / `models_py314.py`，`VERSION_MODULES` 加两级；删 3.10/3.11/3.12 的存量副本 | **已落地**（2026-11-18）：五个版本文件各只含一个 `TypingProbeN`（其余名字回落基线 `models.py`）；`VERSION_MODULES` 按 314→312→311→310→39 排序；`test_version_probes{,_async}.py` 断言各探针落回自己的文件、常规名字回落基线。本地 3.14 / 3.15 跑通；3.13 的回落由「最新 required ≤ 当前」规则覆盖（未在本机跑） |
| 8 | 删 `fixture_types.py`、17 个 `Definition`、`TypeCase`/`TypeTestModel` 旧表 | **已完成**（2026-11-18）：`fixture_types.py` 已删除，助手迁入五组本地；basic 原有 17 个 `Definition` 在阶段 1 清除；`type_rows_models.py`、`TypeCase`/`TypeTestModel` 四个模型、`TYPE_ROW_FIXTURES`、依赖它们的 `test_fields{,_async}.py` 与 `crud` 的 `test_type_case_crud` 一并删除，conftest/models 中的引用同步清理。四组的 `Definition` 属各自组的建表来源，不在 basic 旧表清理范围内 |

每个阶段独立提交、推送即触发 CI，不等结果继续下一阶段。

**阶段 2a 是关键路径**：它决定 bare 能不能存在。若 core 的推断迟迟不落地，
阶段 3–5 的 bare 部分只能空转，届时要么推迟，要么先只做 annotated（不要退回到
「bare = 只给 UseSqlType」——那会让产品承诺与夹具事实脱节）。**阶段 2b 是长内容组与
微秒补充的前置**，可以 2a 并行，但必须早于阶段 5。

---

## 11. 已定与待探索

**已定**：

1. **bare = 字面零注记**（§2 P2）。它是「写个类就能建表」这一产品承诺的验收夹具，
   承诺最终写进项目 README。2026-11-17：core 的存储类型推断已落地
   （`suggested_data_types()` 24 键全答、无 `None`），因此 bare 不再受阻；
   本条从「待实现」改为「已具备、待阶段 3 接入」。
2. **不额外加「零注记必须报错」的契约测试**：既然承诺是「能建表」，断言就必须是
   「能建表且与等价注记逐字相同」，而不是断言旧的失败行为。
3. **类型概念的能力检查走临时元数据类**（§8.1），core 接口落地后再删壳
   （`ddl-source-capabilities.md`）。
4. **长内容取 16 000 字符，且这一组只有 annotated 变体**；容量由
   `TextType(length=16000)` / `BlobType(length=16000)` 声明（语义为下限、方言向上取档、
   4 B/字符换算），前提是阶段 2b。`> 64 KB` 的 LOB 档位属该阶段的后续。
5. **毫秒是默认，微秒是补充能力**：`DefaultTimestampMixin` → `TimestampType(precision=3)`；
   Firebird 接受 precision ≤ 4 并渲染 `TIMESTAMP`，其 1/10000 秒测试留在 firebird 仓；
   微秒夹具是独立的 `microsecond_rows`（2 列），由 `supports_microsecond_timestamp()`
   决定是否跳过（Firebird 答 False，跳过并指名）。
6. **`Mapped*` 按 P2 归入 annotated 变体**，不再独立成组。
7. **C 层的表统一称「建议存储类型表」**（`suggested_data_types()`）：它只在字段未声明
   `UseSqlType` 时提供默认，显式声明永远优先，用户可完全不使用；建议渲染失败时**报错
   指名表与列**，不静默降级。
8. **identity 退出 bare/annotated 变体轴**（2026-11-18 实测）：`Optional[int]` + 默认
   `pk_auto_generated()` 即表达"数据库赋值",与显式 `IdentityAttribute()` 派生的 DDL 逐字相同。
   共享夹具不再写 `IdentityAttribute`;自增行为由 `supports_database_assigned_integer_column()`
   门控,具体 DDL 机制由各后端自己的契约测试覆盖（PostgreSQL 的 SERIAL 亦属后者）。
9. **三个类型组已建,并接受以下可移植性取舍**（2026-11-18）：
   - `types_complex/` 表名用 `complex_rows`（与 §3 初稿的 `complex_rows_default` 不同，以代码为准）；
   - `Vector/Range/BitString` 只做 annotated，用 `JsonType`/`TextType` 载体，原生维度/元素/位宽语义留给后端专用类型；
   - geometry 用 `CustomType(raw="GEOMETRY")` 表示通用子类型，原生 `POINT`/SRID 不进共享夹具；
   - `timedelta` 在 SQLite 无 DML 转换器，往返用例存 NULL，待 core 补转换器后改为真实时长；
   - `types_long_content/` 的 DB 用例按需请求 `schema`（**非 autouse**），因此方言拒绝 XML 时只有 DB 用例跳过，声明级断言照常执行。

**待探索（已另立计划）**：

- `minimal-definition.md`：零注记建表、四个默认值（`str` 长度、`int` 宽度、
  整数主键由数据库赋值、`Decimal` 精度）、推断与 `suggested_column_types()` 同源。
- `ddl-source-capabilities.md`：`DDLSource.required_capabilities()` 与
  `dialect.supports(concept)` 的统一通道。
- `type-capacity-and-precision.md`：五个内容类型的 `length`、档位映射与 4 B/字符换算、
  毫秒默认与微秒开关、Firebird precision ≤ 4。

---

## 12. 字段表达式组：`expressions/`（DML / DDL / 表达式三面齐）

前三个类型组管的是「值怎么存、怎么往返」。还差一面：**`Model.c.<field>` 拿到的是哪种列类、
能做哪些运算**。这一组补上它，于是本目录服务的测试覆盖 DML（读写）、DDL（建表）与
字段表达式（查询构造）三面。

**不新增表，不新增模型**：本组复用 `users` / `typed_users` / `complex_rows` 等既有表，
只断言它们的列表达式，因此**没有自己的 DDL/DML 操作**，`TableFixture.source` 全为 `None`。

| 断言 | 内容 | 依赖 |
|---|---|---|
| X1 列类来自声明 | `Model.c.<field>` 的类 == 该方言 `suggested_column_types()[<Python 类型>]` | 主表 24 键 |
| X2 正向运算 | 每个值族一个必须能渲染的运算：`IntegerColumn` 的算术、`StringColumn.like`、`TimestampColumn` 比较、`JSONColumn.json_path`、`ArrayColumn` 元素、几何/向量族各自的首个运算 | 列类存在 |
| X3 负向运算 | 不该有的运算必须**不存在**（`JSONColumn` 没有 `like`、`XMLColumn` 不可比较），不是「运行时数据库报错」 | 列类存在 |
| X4 列名映射 | `UseColumn` 改名的字段在表达式中用**列名**而不是字段名 | 既有 |
| X5 同步/异步同源 | 同表两模型的 `c.<field>` 解析到同一个类 | P4 |
| X6 后端差异**显式** | 某族在 B 层答 `None` 时，X2 的该条**跳过并指名**「`<方言>` 对 `<值族>` 没有运算类」；方言漏答是失败，不是跳过 | §9 |

要点：

- **X1 是「列类不是硬编码」的验收**：断言的是「模型声明 → 方言答案」这条路，
  所以换后端时期望值随之变化，测试体不变。
- **X2/X3 是「运算集」的验收**：只断 SQL 文本与可调用性，不执行（DB-free，走 `dialect` 夹具），
  因此本组不占数据库、可与其它目录并行。
- 复杂族在 B 层答 `None` 时（SQLite/Oracle 等），X2 跳过、`Model.c.x` 本身**照旧报错** ——
  这正是「存得下但算不了」的显式形态（E-2）。
- 迁移阶段：随 §10 的 6 号阶段一起做（列类先于表达式测试落地）。

---

## 附：版本文件机制现状与目标

`fixtures/__init__.py` 的 `resolve(name)` 按 `314 → 312 → 311 → 310 → 39 → 基线`
顺序取第一个定义该名字的模块；因此版本文件只需覆盖**语法不同**的类，无需手抄整个矩阵。
`resolve()` 的回落不会因为「文件存在」而生效，只会因为「文件里定义了这个名字」而生效。
阶段 7 后这一回落链已落地，并由 `test_version_probes{,_async}.py` 以「最新
required ≤ 当前解释器」规则验证：3.13 落 3.12、3.14/3.15 落 3.14。

| 文件 | 迁移前 | 现状（阶段 7 已落地） |
|---|---|---|
| `models.py` | 3.8 基线，66 类 + 17 Definition | 聚合并 re-export 各组模型，`resolve()` 回落目标 |
| `models_py39.py` | 不存在 | `TypingProbe39`（PEP 585 `list[str]` / `dict[str, int]`） |
| `models_py310.py` | 35 类手抄（`X \| Y`） | `TypingProbe310`（PEP 604 联合注解） |
| `models_py311.py` | 35 类手抄（`Self`） | `TypingProbe311`（`Self` + `LiteralString`） |
| `models_py312.py` | 35 类手抄（`@override`、PEP 695） | `TypingProbe312`（`@override`） |
| `models_py314.py` | 不存在 | `TypingProbe314`（PEP 649/749 惰性注解 `__annotate__`） |

3.13 与 3.15 不建文件：它们在本轴上不引入新语法/新语义，回落到 3.12 / 3.14 即可。
版本文件的判据只有一条 —— **能否写出基线写不出的、且与列声明相关的语法**；
写得出才建文件，写不出就不建，避免出现一批只改注释的版本副本。
