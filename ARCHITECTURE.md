# Architecture

## 总览

```text
                     Web UI
                       |
                       v
                AI Platform API (FastAPI)
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
  Model Gateway       RAG       Agent Router
        |              |              |
        |              |       +------+------+
        |              |       |      |      |
        v              v       v      v      v
   LLM Providers   Vector DB  ERP  Safety  Equipment
   (mock / OpenAI-  (Chroma)   Tool   Tool   Tool
    compatible)
        \              |              /
         \-------------+-------------/
                       v
                Answer + Sources
                       |
              +--------+--------+
              v                 v
          Audit Log         Metrics
```

## 组件

| 组件 | 模块 | 说明 |
|---|---|---|
| Model Gateway | `app/gateway/` | 统一 LLM 访问层。业务代码只依赖 `ModelGateway`，不直接 import provider SDK。默认 `MockProvider`，可切 OpenAI-compatible（DeepSeek/Qwen/Ollama）。 |
| Embedding | `app/embeddings/` | 可替换 `EmbeddingProvider` 抽象（`embed_documents` / `embed_query`）。默认离线 `MockEmbeddingProvider`（hash n-gram，零 API Key），可切 OpenAI-compatible `/embeddings`（`app/embeddings/openai_compatible.py`）。`build_embedding_provider()` 按配置构造。 |
| RAG | `app/rag/` | ingest（`ingest.py` + `extractor.py`：Markdown/TXT/PDF）→ heading 感知 chunk（`chunker.py`：800–1200 字，overlap 100–200）→ embedding → Chroma persistent client（`store.py`）→ 混合检索（`retriever.py`：向量 + 词面重合融合，top_k=5）→ 带 `[n]` 引用的回答（`pipeline.py` + `prompt.py`）。检索结果必须带 document_id / title / section / page / source / score；找不到依据时回答「知识库没有足够信息」。 |
| 知识库服务 | `app/services/knowledge_service.py` | 组合 ingest / documents / search 三个用例；API 通过 `get_knowledge_service` 依赖注入，测试可指向临时 Chroma 目录与 mock embedding。 |
| Agent | `app/agent/` | Tool 协议 + ToolResult（`tools/base.py`）→ 白名单 Tool Registry（`registry.py`：重名/未知工具明确报错）→ Tool Executor（`executor.py`：validate → lookup → execute，异常转受控 failure）→ Agent Runtime（`runtime.py`：AgentState / Agent Loop / trace，`max_steps` + `max_tool_calls` 安全限制）。工具白名单（Day 3）：`knowledge_search`（封装 RAG 检索，citation 一路保留）、`document_lookup`；业务 Tool 逐日增加。Prompt policy（`prompts.py`）：优先知识库、不编造、无依据时明确说明。 |
| 业务数据库 | `app/db/` + `data/synthetic/` | `models.py`（9 张表 ORM，唯一事实来源）+ `database.py`（SQLite engine/session/singleton）+ `seed.py`（确定性播种：`schema.sql` 为参考 DDL，`seed.json` 提供目录 + 生成参数，时间序列相对「今天」生成）+ `queries.py`（固定参数化聚合查询）。**LLM 无法生成任意 SQL / 表名 / 列名**，只能选择白名单 operation。 |
| RBAC | `app/auth/` | Bearer Token → 用户 → 角色 → 权限：`auth.py`（3 个演示 token）、`permissions.py`（Permission 枚举 + 角色矩阵 + 路由/工具映射）、`dependencies.py`（`get_current_user` / `require(permission)`）。缺/坏 token → 401，权限不足 → 403（并写审计）。Tool 级权限在 `app/agent/executor.py` 内二次执行，路由被绕过也不会漏。 |
| 审计 / 指标 / 日志 | `app/observability/` | `middleware.py`（纯 ASGI：request_id、计时、指标、`X-Request-ID`）、`logging.py`（JSON 结构化日志 + request_id ContextVar）、`metrics.py`（进程内指标，`GET /metrics` 输出 JSON）、`audit.py`（`AuditLog`：API/Agent/Tool 三类事件，脱敏 input_summary，写 `audit_logs` 表 + `GET /api/audit` 读取）。 |
| 统一错误 | `app/api/errors.py` | `PlatformError` 层次（401/403/404/409/500）+ 四类 exception handler，输出 `{detail, request_id, error:{code,message,details}}`；不泄露 traceback、连接串与密钥。 |

## 请求生命周期（Day 4）

```text
Request
  → RequestContextMiddleware     生成/沿用 request_id，计时，写 http.request 日志与指标
  → Route                        公开：/health /metrics；其余挂 Depends
  → get_current_user             Bearer token → CurrentUser（401 时统一错误信封）
  → require(permission)          角色矩阵检查（403 + 审计 denied 行）
  → handler                      业务用例（chat / knowledge / agent / audit）
  → AgentRuntime                 有限步 loop（max_steps / max_tool_calls）
  → ToolExecutor                 查工具 → 查权限（tool 边界）→ 校验参数 → execute
  → BusinessQueryTool            固定 operation → queries.py 参数化 SQL → SQLite(合成)
  → AuditLog                     tool.call / agent.run / api 行（request_id 串联）
  → 响应                          {request_id, …} + X-Request-ID 头
```

一次提问可以只用一个 `request_id` 从 HTTP 追到工具调用与审计行：
`GET /api/audit?request_id=…`（或 `GET /api/audit/{request_id}`）。

## 权限与工具边界

| 层 | 位置 | 失败表现 |
|---|---|---|
| 路由 | `require(Permission.X)` | 401 / 403 + 统一错误信封 + 审计 `denied`（仅 403，401 无 user_id 不落库） |
| Agent 工具 | `ToolExecutor.execute(actor=…)` | HTTP 200，`tool_calls[].success=false`、`error_code=PERMISSION_DENIED`，Agent 用一段说明收尾，审计写 `tool.call=denied` + `agent.run=denied` |
| 数据 | `app/db/queries.py` | 只有固定 operation + 参数绑定；参数越界由 Pydantic 拦为 `INVALID_ARGUMENTS`，DB 故障转 `ToolResult(success=false)` |

设计取舍：演示 token 是**故意公开**的固定常量（无 JWT / 登录 / SSO / 多租户），
为的是零门槛复现 RBAC 链路；`Permission` 枚举、角色矩阵与 tool 边界检查与真实鉴权方案解耦，
接入真实身份提供方时可整体保留。

## 安全边界

- 高风险业务只做分析 / 辅助决策，不接真实 DCS，不做工业控制。
- 知识库只允许公开资料（SPEC 6.1）；`data/documents/` 每篇文档带 YAML front matter
  （document_id / title / source / url / published_at），README.md 与不支持的类型跳过。
- 不提交任何 secret 到 Git；`.env` 默认全部 mock，无需 key 即可运行测试与 UI。

## Day 5 — Web Console 与前后端交互

```text
浏览器 / Web Console (nginx :3000, React SPA)
   │  静态资源 + 反代 /api /health /metrics
   ▼
FastAPI (ASGI 中间件：request_id → 鉴权 → 路由 → 业务)
   │
   ├── chat / agent / knowledge / models / users / audit / metrics / health
   ├── AgentRuntime（有限步 loop）
   │      ├── ToolRegistry → 白名单 Tool
   │      ├── ToolExecutor（工具级 RBAC 二次校验 + 参数校验 + 异常转受控失败）
   │      └── Trace（llm / tool_call / final / stopped）
   ├── RAG（knowledge_search → Chroma → citation）
   ├── 合成 SQLite（operation 白名单 + 参数化 SQL：ERP / Safety）
   ├── AuditLog（request_id 贯穿：http.request / agent.run / tool.call）
   └── Metrics（请求 / 工具 / Agent / 拒绝 / 延迟）
```

**Web Console 页面与 API 对应**

| 页面 | 数据源 | 边界 |
|---|---|---|
| Dashboard | `GET /health` + `GET /metrics` | 公开，无需 token；状态卡 + 指标面板 + 端点延迟 |
| Agent Playground | `POST /api/agent/run` | 走完整 Agent loop，渲染 trace / 工具调用 / sources / 引用 |
| Knowledge | `GET /api/knowledge/documents` + `POST /api/knowledge/search` | 检索结果 + citation；ingest 仅 admin（其余角色 UI 禁用，后端仍 403） |
| Audit | `GET /api/audit` + `GET /api/audit/{request_id}` | 按 request_id 追踪；operator 无 `audit:read` → 403 受控页 |
| Settings | 角色矩阵 + 演示 token | 前端切角色 = 切换 Bearer token；后端鉴权逻辑不变 |

前端角色切换只改请求头里用的 demo token，**不绕过任何安全边界**；同一问句换 operator 立刻看到
工具级 `PERMISSION_DENIED`（后端 `ToolExecutor` 拒绝，非前端假象）。

### 一次企业知识问答在 Day 5 之后如何穿过全部层

```text
Web Console (浏览器)
  → Agent Playground 输入「恒光主要有哪些业务？」
  → POST /api/agent/run (Authorization: Bearer demo-admin-token)
  → request_id 生成（中间件）
  → AgentRuntime.loop（max_steps=5 / max_tool_calls=8）
  → LLM(mock) 判定调用 knowledge_search（arguments 由 Pydantic 校验）
  → ToolExecutor：白名单查工具 → 权限校验（operator 会在此被拒）→ 参数校验 → 执行
  → RAG search → Chroma top_k=5（heading 感知 chunk + 混合检索）
  → 引用 [n] + document metadata（title / section / source / url）
  → LLM 生成最终回答 + sources
  → Trace：llm / tool_call / final（含 latency_ms、status、error_code）
  → AuditLog：agent.run + tool.call + http.request（同一 request_id）
  → Metrics：请求 +1、工具调用 +1、延迟更新
  → Web Console 渲染：回答、trace 时间线、工具调用、引用、指标
```
