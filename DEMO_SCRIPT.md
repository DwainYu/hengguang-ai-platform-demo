# Demo Script（5–8 分钟）

> 面试演示脚本，见 SPEC 第 15 节。本文件随实现进度更新。

## Step 1 — 30 秒：定位项目

> 这是我针对贵公司的 AI 平台岗位做的一个技术原型。因为真实企业内部数据不能使用，
> 所以知识库使用公开资料，ERP、安全等数据使用的是合成数据。
> 我的重点不是做一个聊天机器人，而是验证模型、知识、业务系统和 Agent 能否形成一个统一 AI Platform。

## Step 2 — 60 秒：Dashboard（平台层）

```bash
export ADMIN="Authorization: Bearer demo-admin-token"
export OPERATOR="Authorization: Bearer demo-operator-token"
curl -s http://localhost:8000/metrics            # request_count / success / latency / tool 计数
curl -s -H "$ADMIN" http://localhost:8000/api/models   # provider 可用性 + 4 个工具 + 该角色允许的调用
```

> 平台层先统一模型接入、日志和基础监控：`/metrics` 是进程内指标快照，
> `/api/models` 同时返回工具白名单与当前角色被允许的调用，前端无需了解后端实现。

## Step 3 — 90 秒：RAG

先 ingest（首次启动执行一次）：

```bash
curl -X POST http://localhost:8000/api/knowledge/ingest -H 'Content-Type: application/json' -d '{}'
```

输入：`恒光主要有哪些业务？`（`POST /api/knowledge/search`）

展示回答、`citations`（来源 title + section）、每个 chunk 的 document_id / score / content。

> 这里不是让模型凭记忆回答，而是先从企业公开资料（公司公开简介、2025 年报、2026 半年报）中
> 召回 Top-K chunks，再让模型基于检索内容生成带 [n] 引用的回答；
> 问知识库里没有的问题时，系统明确说明「当前知识库没有足够信息」。

## Step 4 — 90 秒：ERP Agent（合成数据）

```bash
curl -s -X POST http://localhost:8000/api/agent/run -H "$ADMIN" -H 'Content-Type: application/json' \
  -d '{"message": "最近30天主要原材料采购价格如何变化？"}'
```

展示 Agent → `erp_purchase_analysis`（operation=`purchase_price_trend`）→ 固定参数化 SQL
→ 结果表格 + 变化率 → LLM summary；再问一句供应商集中度
（`最近30天哪个供应商供货最多？` → `supplier_summary`）。

> 模型不直接执行任意 SQL，只能选 7 个白名单 operation；数据是 SQLite 里
> 由 `data/synthetic/seed.json` 确定性生成的合成 ERP（约 330 张采购订单 / 120 天，重启不丢）。

## Step 5 — 90 秒：Safety Agent（全角色可用）

```bash
curl -s -X POST http://localhost:8000/api/agent/run -H "$OPERATOR" -H 'Content-Type: application/json' \
  -d '{"message": "最近一个月哪个区域安全问题最多？"}'      # safety_incident_analysis / incident_by_area
```

再问 `A车间最近安全问题为什么增加？相关安全制度有哪些？`，展示
Safety Tool + Knowledge Tool（RAG 制度依据）+ LLM synthesis。

> 安全数据同样是合成数据；A 车间事件占比最高（演示数据刻意做出的信号）。

## Step 6 — 90 秒：平台工程（RBAC + 审计 + 错误处理）

```bash
# 1) 无 token / 坏 token → 401，统一错误信封
curl -s -i http://localhost:8000/api/models | head -3
# 2) operator 问 ERP → 权限在 Tool 边界拒绝，Agent 不崩，回答说明原因
curl -s -X POST http://localhost:8000/api/agent/run -H "$OPERATOR" -H 'Content-Type: application/json' \
  -d '{"message": "最近30天哪个供应商供货最多？"}' | python3 -m json.tool | head -20
# 3) operator 读审计 → 403；manager/admin → 200，可分页可过滤
curl -s -H "$OPERATOR" http://localhost:8000/api/audit | python3 -m json.tool
curl -s -H "$ADMIN" 'http://localhost:8000/api/audit?status=denied&page_size=5' | python3 -m json.tool
# 4) 同一个 request_id 追到底（HTTP → Agent → Tool → Audit）
curl -s -H "$ADMIN" http://localhost:8000/api/audit/<request_id> | python3 -m json.tool
# 5) 指标 + 结构化日志
curl -s http://localhost:8000/metrics | python3 -m json.tool | head -20
```

> RBAC 不只在路由上：工具权限在 `ToolExecutor` 里再检查一次，所以越权调用一定留下
> `denied` 审计行，同时 Agent 仍能正常收尾。审计只存参数摘要与统计，不存 API Key、
> token 和文档全文。

展示 Docker Compose 部署（`docker compose up`）。

> 如果进入真实环境，我会把 ERP/OA/DCS 等真实接口通过 Tool/Connector 接入，
> 但高风险生产控制仍然留在原有工业控制系统和人工审批链路中，AI 主要承担知识检索、数据分析和辅助决策。
