# Demo Script（5–8 分钟）

> 面试演示脚本，见 SPEC 第 15 节。本文件随实现进度更新。

## Step 1 — 30 秒：定位项目

> 这是我针对贵公司的 AI 平台岗位做的一个技术原型。因为真实企业内部数据不能使用，
> 所以知识库使用公开资料，ERP、安全等数据使用的是合成数据。
> 我的重点不是做一个聊天机器人，而是验证模型、知识、业务系统和 Agent 能否形成一个统一 AI Platform。

## Step 2 — 60 秒：Dashboard

展示 Models / request count / success rate / latency。

> 平台层先统一模型接入、日志和基础监控。

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

## Step 4 — 90 秒：ERP Agent

输入：`最近 30 天原材料采购价格有什么变化？`

展示 Agent -> ERP Tool -> SQL/aggregation -> LLM summary。

> 模型不直接执行任意 SQL，而是只能调用白名单 Tool。

## Step 5 — 90 秒：Safety Agent

输入：`最近一个月哪个区域安全问题最多？` 再问 `A车间最近安全问题为什么增加？相关安全制度有哪些？`

展示多工具：Safety Tool + Knowledge Tool + LLM synthesis。

## Step 6 — 60 秒：平台工程

展示 Model Gateway、RBAC、Audit Log、Docker Compose。

> 如果进入真实环境，我会把 ERP/OA/DCS 等真实接口通过 Tool/Connector 接入，
> 但高风险生产控制仍然留在原有工业控制系统和人工审批链路中，AI 主要承担知识检索、数据分析和辅助决策。
