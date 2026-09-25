# data/synthetic — 合成业务数据（synthetic demo data）

> **全部数据均为人工构造的合成数据**，与湖南恒光科技股份有限公司（301109.SZ）的真实
> 采购、库存、安全、设备数据**没有任何关系**，仅用于演示平台的业务工具链路。
> 供应商名称、物料价格、事件描述均为虚构；不含任何真实企业内部数据、账号或密钥。

## 文件

| 文件 | 作用 |
|---|---|
| `schema.sql` | 参考 DDL（9 张表 + 索引），与 `app/db/models.py` 的 ORM 定义保持列级一致（有测试校验） |
| `seed.json` | 静态目录 + 生成参数：用户 / 供应商 / 物料 / 库存快照 / 安全配置 / 设备 + 时间序列生成规则 |

`purchase_orders` 与 `safety_incidents` 是**时间序列**，不写在 JSON 里，由
`app/db/seed.py` 按 `seed.json` 的参数（`random_seed`、`days_back`、
`purchase_orders_per_week`、`safety_incidents_per_week`）**确定性生成**，
因此相对日期是「今天」而非某个固定日期，`最近30天` 这类查询永远有数据。

## 表与数量级（默认参数，as-of 今天）

| 表 | 行数 | 内容 |
|---|---|---|
| `users` | 3 | admin_demo / manager_demo / operator_demo（演示 token，见 `app/auth/auth.py`） |
| `suppliers` | 8 | 虚构供应商：名称、编码、品类偏好、评级、状态 |
| `materials` | 10 | 原盐、硫精砂、液碱（32%）、盐酸、硫酸、双氧水、蒸汽、包装袋（吨袋）、次氯酸钠、三氯化铁（含品类、单位、基准价、价格漂移） |
| `purchase_orders` | ~330（120 天，20 单/周） | 单号、日期、物料、供应商、数量、单价、总金额、状态；近 30 天约 80 单 |
| `inventory` | 9 | 仓库、物料、当前数量、更新时间（快照） |
| `safety_incidents` | ~120（120 天，7 起/周） | 事件编号、日期、区域、类别、严重度、状态、标题/描述、是否闭环；近 30 天约 30 起 |
| `equipment` | 6 | 设备台账（Day 5+ 备用） |
| `maintenance_records` | 6 | 维修记录（Day 5+ 备用） |
| `audit_logs` | 运行时写入 | API / Agent / Tool 调用审计（见 `app/observability/audit.py`） |

## 重新生成

```bash
# 默认：写入 DATABASE_URL（./data/runtime/app.db），已 seeded 则跳过
uv run python -m app.db.seed

# 重建（清空业务表后按今天的日期重新生成时间序列）
uv run python -m app.db.seed --force

# 指定数据库与锚点日期（可复现：random_seed 固定，同一 as_of 结果完全一致）
uv run python -m app.db.seed --url sqlite:///./data/runtime/app.db --as-of 2026-09-26 --force
```

服务启动时 `app/main.py` 的 lifespan 会自动建表并在空库时播种，无需手工执行。

数据库文件写在 `data/runtime/`（已 gitignore），本目录只存放**只读的种子输入**。
