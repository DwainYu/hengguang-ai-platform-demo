# Demo Script（5–8 分钟，Web Console 驱动）

> 面试演示脚本。Day 5 起整个演示以 **Web Console** 为主线：
> `docker compose up --build` 后打开 `http://localhost:3000`，右上角可随时切换角色。
> 全程不写一行代码、不翻后端文件；每个步骤讲的都是「平台层做了什么事」。
> 对应截图见 `screenshots/` 目录。

## Step 1 — 30 秒：定位项目

> 这是我针对贵公司的 AI 平台岗位做的技术原型。真实企业内部数据不能用，
> 所以知识库用公开资料，ERP、安全数据全部是合成数据。
> 重点不是做聊天机器人，而是验证**模型、知识、业务系统、Agent 能否收敛进同一个 AI 平台层**，
> 并把权限、审计、指标、失败处理做对。

（打开 `http://localhost:3000`，首页即 Dashboard。）

## Step 2 — 60 秒：Dashboard（平台层状态）

> 这一屏回答「平台现在健不健康」：API 状态、模型 Provider、知识库状态、
> 请求数 / Agent 运行 / 工具调用 / 错误数，以及按端点的平均延迟。
> 数据全部来自 `GET /health` 与 `GET /metrics`，页面 15 秒自动刷新。

> 强调：**可观测性是平台的一部分**，不是事后补的脚本。

## Step 3 — 90 秒：Agent Playground + RAG

1. 切到 **Manager**，输入「恒光主要有哪些业务？」
2. 展示回答正文带 `[n]` 引用，右侧展示：
   - **Trace 时间线**：LLM → 请求调用工具 → 工具结果（5 chunks）→ 最终回答
   - **工具调用**：`knowledge_search` 参数 / 成功 / 结果数 / 延迟
   - **Sources**：每条引用有标题、章节、来源、URL
3. 说明：回答只基于检索到的公开资料，无依据时会明确说「知识库没有足够信息」，不编造。

> 这一屏回答「模型能不能凭记忆回答企业事实」——不能，所以走 RAG + citation。

## Step 4 — 60 秒：业务工具（ERP + Safety）

1. 仍为 Manager：「最近30天主要原材料采购价格有什么变化？」
   → `erp_purchase_analysis`（operation 白名单 + 参数化 SQL 查合成 SQLite）→ 表格化结果 + 回答。
2. 切到 **Operator**：「最近一个月哪个区域安全问题最多？」
   → `safety_incident_analysis` 成功（operator 可用安全工具）。

> 关键设计：**LLM 只能选固定 operation 传参数，写不了 SQL、传不了表名列名**。

## Step 5 — 90 秒：RBAC 权限边界（本次演示的高光）

1. 仍为 **Operator**，问「最近30天主要原材料采购价格有什么变化？」
2. Agent 回答正常收尾（HTTP 200、不崩），但工具调用处显示 **`PERMISSION_DENIED`**：
   权限在 `ToolExecutor` 边界被拒，工具根本没执行、没触达数据。
3. 切回 **Manager** 问同一句 → 成功。
4. 说明：前端切角色只是换请求头，**后端才是安全边界**；operator 问 ERP 是「受控拒绝」，
   不是 500、不是把数据漏出去。

## Step 6 — 60 秒：Audit（一个 request_id 追到底）

1. 打开 **Audit** 页（operator 会被 403 —— 顺带展示「审计本身也是受权限保护的」）
2. 表格按 request_id 过滤，点开一行看该请求的 `agent.run` + `tool.call` 完整链路，
   包括刚才那次 `PERMISSION_DENIED` 的记录。
3. 强调：**HTTP / Agent / Tool 三类事件共享同一个 request_id**，出事一条链查到底。

## Step 7 — 60 秒：Knowledge + 指标

1. **Knowledge** 页：文档/chunk 统计、直接检索（结果 + citation）。ingest 仅 admin 可点。
2. 回到 **Dashboard**：刚才所有操作已反映在请求数 / 工具调用 / 延迟上。

## Step 8 — 30 秒：收尾 + 可选真实 LLM

- 总结能力栈：Model Gateway / RAG / Agent / ERP·Safety Tool / RBAC / Audit / Metrics / Docker。
- 可选：展示 `LLM_PROVIDER=openai-compatible` 切到真实 provider（ModelScope DeepSeek）后，
  同一问句由真实模型生成回答，**引用与审计链路完全不变**。
- 收尾话术：平台层已收敛模型、知识、业务、权限、审计；下一步是接真实身份（JWT/SSO）、
  真实业务系统与灰度放量。
