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
