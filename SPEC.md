# Hengguang AI Platform Demo — Implementation Specification

> **项目定位**：面向「湖南恒光科技股份有限公司 AI 平台工程师」岗位的 3–5 天求职技术 Demo。
>
> **目标**：用一个可运行、可演示、可 Docker 部署的最小企业 AI 平台原型，证明对 Model Gateway、RAG、Agent、企业系统集成、权限、审计、监控和私有化部署的理解。
>
> **重要声明**：本项目仅用于技术演示和求职交流。不得接入恒光科技内部系统，不得使用任何内部数据、账号、密钥、业务数据或未公开资料。知识库只使用公开资料；ERP/安全/设备等业务数据全部使用合成数据（synthetic data）。

---

## 0. 给 pi-coding-agent 的执行规则

### 0.1 实现原则

1. **先做最小闭环，再做增强功能**。
2. **禁止过度工程化**：3–5 天 Demo 不引入 Kubernetes、Kafka、Redis、微服务集群、复杂工作流平台等非必要组件。
3. **所有外部模型访问必须通过统一 Model Gateway**，业务层不得直接调用 DeepSeek/Qwen/OpenAI/Ollama SDK。
4. **Agent 工具必须白名单化**。禁止让 LLM 生成并直接执行任意 SQL。
5. **数据库查询全部使用参数化 SQL / 固定 Query Function**。
6. **RAG 必须返回来源引用**，每个 chunk 必须保留 document_id、title、page/section、source。
7. **高风险业务只做分析/辅助决策，不做真实工业控制**。
8. **测试必须可在无真实 LLM Key 的情况下运行**：提供 fake/mock provider。
9. **默认优先简单、可读、可调试的代码，不追求框架炫技**。
10. **每一天结束都必须有可运行结果**，不要把核心功能全部堆到第 5 天。

### 0.2 交付标准

最终仓库应包含：

- 可运行 API
- 可运行前端
- RAG 知识库
- Agent + 3 个业务 Tool
- SQLite 合成业务数据库
- Model Gateway
- Demo RBAC
- Audit Log
- Health Check / Metrics
- Docker Compose
- 测试
- `README.md`
- `ARCHITECTURE.md`
- `DEMO_SCRIPT.md`
- `.env.example`

---

# 1. 项目目标

## 1.1 核心问题

模拟一个化工制造企业在已有 OA / ERP / DCS / 安全生产数字化基础上，引入统一 AI 能力层：

```text
                     Web UI
                       |
                       v
                AI Platform API
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
  Model Gateway       RAG       Agent Router
        |              |              |
        |              |       +------+------+
        |              |       |      |      |
        v              v       v      v      v
   LLM Providers   Vector DB  ERP  Safety Equipment
                              Tool   Tool   Tool
        \              |              /
         \-------------+-------------/
                       |
                       v
                Answer + Sources
                       |
              +--------+--------+
              |                 |
              v                 v
          Audit Log         Metrics
                       
```

## 1.2 核心演示场景

### 场景 A：企业知识 RAG

用户：

> 恒光主要有哪些业务？

系统：

- 检索公开资料
- 调用 LLM
- 返回回答
- 附带来源与页码/章节

### 场景 B：ERP 分析 Agent

用户：

> 最近 30 天主要原材料采购价格有什么变化？

系统：

- Agent 判断需要 ERP Tool
- 调用白名单查询函数
- Python 做聚合计算
- LLM 负责解释结果

### 场景 C：安全分析 Agent

用户：

> 最近一个月哪个区域安全问题最多？

系统：

- Agent 调用 Safety Tool
- 查询合成安全事件数据
- 统计区域 / 严重程度
- LLM 输出分析

### 场景 D：综合分析

用户：

> A 车间最近安全问题为什么增加？相关安全制度有哪些？

系统：

```text
用户问题
  |
  v
Agent
  |
  +--> Safety Tool：统计趋势
  |
  +--> Knowledge Tool：检索安全 SOP / 制度
  |
  +--> LLM：综合分析
  |
  v
回答 + 数据结果 + 文档来源
```

---

# 2. 技术选型

## 2.1 Backend

| 组件 | 选择 | 原因 |
|---|---|---|
| Language | Python 3.11+ | AI/数据生态成熟，开发速度快 |
| Package Manager | uv | 快、简单，适合本项目 |
| API | FastAPI | OpenAPI、自带校验、开发快 |
| Schema | Pydantic v2 | API / Tool 参数校验 |
| HTTP | httpx | Provider API / 外部 API |
| ORM | SQLAlchemy 2.x | 简单、成熟；或 SQLAlchemy Core |
| DB | SQLite | 3–5 天 Demo 足够 |
| Testing | pytest | 快速建立回归测试 |
| Lint/Format | ruff | 一体化 |

## 2.2 LLM / Model Gateway

统一接口：

```python
class ModelProvider(Protocol):
    async def chat(
        self,
        messages: list[dict],
        *,
        model: str,
        temperature: float = 0.2,
        response_format: dict | None = None,
    ) -> ModelResponse: ...
```

Provider 最少实现：

- `OpenAICompatibleProvider`
- `MockProvider`

通过配置支持：

- DeepSeek / Qwen 等 OpenAI-compatible API
- Ollama OpenAI-compatible endpoint（可选）

**要求**：业务代码只依赖 `ModelGateway`，不能直接 import provider SDK。

## 2.3 Embedding / RAG

优先采用可替换的 `EmbeddingProvider` 抽象：

```python
class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...
```

默认实现可以使用：

- OpenAI-compatible Embedding API，或
- 本地 embedding 服务（如 Ollama），或
- 可本地运行的 embedding 模型。

Vector Store：

- Chroma Persistent Client

如果 Chroma 在当前环境安装/运行不稳定，允许替换为 FAISS，但 API 层必须保持不变。

## 2.4 Frontend

- React
- Vite
- TypeScript
- 简单 CSS / 轻量 UI

不要引入大型 UI framework，除非已经在项目环境中可直接使用且不会拖慢开发。

## 2.5 Deployment

- Docker
- Docker Compose
- 单 API 容器 + 单 Web 容器
- SQLite / Chroma 使用 Docker volume 持久化

---

# 3. 功能范围

## 3.1 P0 — 必须完成

- [ ] `/health`
- [ ] `/api/chat`
- [ ] Model Gateway
- [ ] Mock LLM
- [ ] 真实 LLM Provider
- [ ] 文档 ingest
- [ ] RAG retrieval
- [ ] Source citation
- [ ] Agent Router
- [ ] Knowledge Tool
- [ ] ERP Tool
- [ ] Safety Tool
- [ ] SQLite schema + seed
- [ ] 基础 RBAC
- [ ] Audit Log
- [ ] Metrics
- [ ] Docker Compose
- [ ] 前端聊天页
- [ ] Agent trace 展示
- [ ] README / Architecture / Demo Script
- [ ] pytest 测试

## 3.2 P1 — 有时间再做

- [ ] Equipment Tool
- [ ] Model fallback
- [ ] Token / cost estimation
- [ ] Rate limit
- [ ] 管理后台
- [ ] Streaming response
- [ ] 文件上传 UI
- [ ] 简单图表

## 3.3 P2 — 本次禁止扩张

不要实现：

- Kubernetes
- 多租户 SaaS
- 真正企业 SSO
- 实际 ERP/OA 连接器
- 真实 DCS 控制
- 自动执行危险生产操作
- 大规模分布式向量库
- 复杂工作流编排平台
- 微服务拆分

---

# 4. 仓库目录结构

```text
hengguang-ai-platform-demo/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── knowledge.py
│   │   ├── agents.py
│   │   ├── models.py
│   │   ├── audit.py
│   │   └── health.py
│   │
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai_compatible.py
│   │   ├── mock.py
│   │   └── router.py
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai_compatible.py
│   │   └── mock.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── chunker.py
│   │   ├── retriever.py
│   │   ├── pipeline.py
│   │   └── schemas.py
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── executor.py
│   │   ├── schemas.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── knowledge.py
│   │       ├── erp.py
│   │       └── safety.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── seed.py
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── permissions.py
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── audit.py
│   │   └── metrics.py
│   │
│   └── services/
│       ├── chat_service.py
│       └── agent_service.py
│
├── data/
│   ├── documents/
│   │   ├── README.md
│   │   ├── hengguang_public_profile.md
│   │   └── public_reports/
│   ├── synthetic/
│   │   ├── schema.sql
│   │   └── seed.json
│   └── runtime/
│       └── .gitkeep
│
├── web/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── types/
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── tests/
│   ├── unit/
│   │   ├── test_gateway.py
│   │   ├── test_rag.py
│   │   └── test_tools.py
│   └── integration/
│       ├── test_chat.py
│       └── test_agent.py
│
├── docker/
│   └── api.Dockerfile
│
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── DEMO_SCRIPT.md
└── SPEC.md
```

---

# 5. 数据设计

## 5.1 users

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'operator')),
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
```

Demo 用户：

```text
admin_demo      admin
manager_demo    manager
operator_demo   operator
```

## 5.2 audit_logs

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_id TEXT NOT NULL,
    action TEXT NOT NULL,
    tool_name TEXT,
    model_name TEXT,
    input_summary TEXT,
    status TEXT NOT NULL,
    latency_ms INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

注意：不要在 audit log 中记录 API Key、完整敏感文档内容或任何真实企业数据。

## 5.3 suppliers

```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT,
    status TEXT NOT NULL
);
```

## 5.4 materials

```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    category TEXT NOT NULL
);
```

## 5.5 purchase_orders

```sql
CREATE TABLE purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY(material_id) REFERENCES materials(id)
);
```

## 5.6 inventory

```sql
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,
    warehouse TEXT NOT NULL,
    quantity REAL NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(material_id) REFERENCES materials(id)
);
```

## 5.7 safety_incidents

```sql
CREATE TABLE safety_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

## 5.8 equipment

```sql
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_code TEXT NOT NULL UNIQUE,
    area TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    status TEXT NOT NULL,
    last_maintenance_at TEXT
);
```

## 5.9 maintenance_records

```sql
CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    maintenance_type TEXT NOT NULL,
    description TEXT NOT NULL,
    maintenance_date TEXT NOT NULL,
    FOREIGN KEY(equipment_id) REFERENCES equipment(id)
);
```

---

# 6. RAG 设计

## 6.1 文档来源

只允许使用公开资料：

- 公司官网公开介绍
- 公开年报 / 半年报
- 公开新闻
- 公开产品介绍
- 公开技术 / 安全相关资料

文档必须保存 metadata：

```json
{
  "document_id": "hg-annual-report-2025",
  "title": "2025年年度报告",
  "source": "public",
  "url": "https://...",
  "page": 123,
  "section": "公司业务",
  "published_at": "2026-..."
}
```

如果 URL 不稳定，可在 repo 中保存合法下载得到的公开文件，并在 metadata 中记录原始 URL。

## 6.2 Chunk

默认：

```text
chunk_size = 800~1200 Chinese chars
chunk_overlap = 100~200 chars
```

允许按 Markdown heading / PDF page 优先切分。

## 6.3 Retrieval

默认 top_k=5。

检索结果必须包含：

```json
{
  "document_id": "...",
  "title": "...",
  "page": 12,
  "score": 0.82,
  "content": "..."
}
```

## 6.4 Answer policy

RAG 系统提示词必须要求：

1. 优先依据检索内容回答。
2. 找不到依据时明确说“当前知识库没有足够信息”。
3. 不得虚构数据。
4. 给出来源引用。
5. 对预测、建议和事实进行区分。

---

# 7. Agent 设计

## 7.1 Tool Registry

```python
class Tool(Protocol):
    name: str
    description: str

    async def execute(self, args: dict) -> ToolResult: ...
```

注册工具：

```text
knowledge_search
erp_purchase_analysis
safety_incident_analysis
```

可选：

```text
equipment_maintenance_lookup
```

## 7.2 Knowledge Tool

输入：

```json
{
  "query": "恒光主要业务有哪些？"
}
```

输出：

```json
{
  "type": "knowledge_result",
  "sources": [...],
  "context": "..."
}
```

## 7.3 ERP Tool

不要允许 LLM 任意生成 SQL。

定义有限操作：

```text
purchase_price_trend
purchase_top_materials
purchase_top_suppliers
inventory_summary
```

例：

```json
{
  "operation": "purchase_price_trend",
  "days": 30,
  "material": "盐酸"
}
```

内部由 Python 使用参数化 SQL 完成。

## 7.4 Safety Tool

有限操作：

```text
incident_by_area
incident_by_severity
incident_trend
high_risk_incidents
```

## 7.5 Agent Routing

优先顺序：

```text
1. 明确需要企业知识 -> knowledge_search
2. 明确询问采购 / 库存 -> ERP Tool
3. 明确询问安全隐患 -> Safety Tool
4. 综合问题 -> 多工具调用
5. 普通聊天 -> Model Gateway
```

可以采用：

- 规则路由作为 baseline
- LLM tool selection 作为增强

**必须保证即使 LLM tool selection 失败，规则 fallback 仍然可用。**

---

# 8. API 设计

## 8.1 GET /health

响应：

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## 8.2 GET /api/models

响应：

```json
{
  "models": [
    {
      "provider": "deepseek",
      "model": "...",
      "enabled": true
    }
  ]
}
```

不返回 API Key。

## 8.3 POST /api/chat

请求：

```json
{
  "message": "恒光主要有哪些业务？",
  "mode": "auto",
  "model": null
}
```

响应：

```json
{
  "request_id": "req_123",
  "answer": "...",
  "mode": "agent",
  "model": "...",
  "sources": [],
  "tool_calls": [
    {
      "tool": "knowledge_search",
      "status": "success"
    }
  ],
  "latency_ms": 1220
}
```

## 8.4 POST /api/knowledge/ingest

仅 admin 可调用。

请求：

```json
{
  "path": "data/documents"
}
```

响应：

```json
{
  "documents": 8,
  "chunks": 132,
  "status": "completed"
}
```

## 8.5 GET /api/knowledge/documents

返回文档列表与 chunk 统计。

## 8.6 GET /api/audit

仅 admin / manager。

Query：

```text
?page=1&page_size=50&tool=safety
```

## 8.7 POST /api/agent/run

用于前端展示 Agent trace。

请求：

```json
{
  "message": "最近一个月哪个区域安全问题最多？"
}
```

响应：

```json
{
  "request_id": "req_xxx",
  "plan": [
    "safety_incident_analysis"
  ],
  "steps": [
    {
      "tool": "safety_incident_analysis",
      "input": {"operation": "incident_by_area", "days": 30},
      "output": {"...": "..."},
      "latency_ms": 42
    }
  ],
  "answer": "..."
}
```

---

# 9. RBAC 设计

## admin

允许：

- 所有知识库操作
- ingest
- Agent
- ERP
- Safety
- Audit
- Models

## manager

允许：

- 知识库查询
- Agent
- ERP
- Safety
- Audit read

不允许：

- ingest
- 用户管理

## operator

允许：

- 知识库查询
- Safety summary

不允许：

- ERP 敏感分析
- Audit
- ingest

鉴权可以使用简单 Bearer Token：

```http
Authorization: Bearer demo-manager-token
```

本项目是 Demo，因此不要求实现完整 OAuth2/OIDC。

---

# 10. Observability

至少记录：

```text
request_id
user
endpoint
model
mode
tool
latency_ms
status
created_at
```

## Metrics

提供最简单的内存统计 / Prometheus-style endpoint 均可：

- request_count
- success_count
- error_count
- avg_latency_ms
- tool_call_count

如果时间不足，优先保证 audit log，metrics 可以简单实现。

---

# 11. 前端要求

只做 3 页。

## 11.1 Dashboard

显示：

```text
Models
Requests
Success Rate
Avg Latency
Tool Calls
```

## 11.2 AI Workspace

核心布局：

```text
+------------------------------------------------+
| Hengguang AI Platform                         |
+------------------------------------------------+
| Chat                                           |
|                                                |
| User: 最近一个月哪个区域安全问题最多？       |
|                                                |
| Agent Trace                                    |
|  ├─ Safety Tool                                |
|  └─ SQL Analysis                               |
|                                                |
| Answer                                         |
| A车间 12条，B车间 7条...                      |
|                                                |
| Sources                                        |
+------------------------------------------------+
```

## 11.3 Knowledge

显示：

- 文档数量
- chunk 数量
- 文档标题
- source
- page

如果有时间，支持 admin ingest。

---

# 12. Docker

## docker-compose.yml

建议：

```yaml
services:
  api:
    build:
      context: .
      dockerfile: docker/api.Dockerfile
    env_file:
      - .env
    volumes:
      - ./data/runtime:/app/data/runtime
      - ./data/documents:/app/data/documents:ro
    ports:
      - "8000:8000"

  web:
    build:
      context: ./web
    depends_on:
      - api
    ports:
      - "3000:80"
```

不要要求 Docker 中自带真实模型。

模型通过环境变量连接外部 OpenAI-compatible API 或宿主机 Ollama。

提供：

```env
LLM_PROVIDER=mock
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
EMBEDDING_PROVIDER=mock
EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=
DATABASE_URL=sqlite:///./data/runtime/app.db
CHROMA_PATH=./data/runtime/chroma
```

默认 `LLM_PROVIDER=mock`，保证首次 clone 后可以运行测试和 UI。

---

# 13. 测试要求

## 13.1 Unit

至少：

```text
test_gateway_provider_switch

test_mock_provider

test_chunking

test_retrieval_metadata

test_erp_tool_parameter_validation

test_safety_tool_parameter_validation

test_role_permissions
```

## 13.2 Integration

至少：

```text
test_health

test_chat_with_mock_provider

test_rag_query_with_mock_embedding

test_agent_safety_query
```

测试不得依赖真实 API Key。

---

# 14. 5 天开发计划

## Day 1 — Platform Skeleton

### 目标

完成：

- FastAPI
- uv 项目
- config
- ModelProvider
- MockProvider
- OpenAI-compatible Provider
- `/health`
- `/api/chat`
- Docker API
- 基础 pytest

### 验收

```bash
uv run pytest
```

通过。

```bash
curl http://localhost:8000/health
```

返回 `status=ok`。

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好"}'
```

成功返回回答。

---

## Day 2 — RAG

### 目标

- 文档目录
- Markdown/PDF ingest
- chunker
- embedding provider
- Chroma
- retriever
- citation
- `/api/knowledge/ingest`
- `/api/knowledge/documents`

### 数据

放入少量公开资料即可，不要求完整收集公司全部资料。

推荐：

- 公司公开简介
- 一份公开年报
- 一份公开半年报
- 2–3 篇公开新闻/产品资料

### 验收

输入：

> 恒光主要有哪些业务？

必须返回：

- 基于知识库的回答
- 至少 1 个来源
- source title
- page/section（若可获得）

---

## Day 3 — Agent + Synthetic ERP/Safety

### 目标

- SQLite
- seed synthetic data
- Tool Registry
- Knowledge Tool
- ERP Tool
- Safety Tool
- Agent Router
- Agent trace API

### 验收

以下 3 个问题必须正确走对应工具：

```text
恒光主要有哪些业务？
-> knowledge_search

最近30天原材料采购价格变化如何？
-> erp_purchase_analysis

最近一个月哪个区域安全问题最多？
-> safety_incident_analysis
```

---

## Day 4 — Platformization

### 目标

- RBAC
- Bearer Token
- Audit Log
- Metrics
- Model list
- fallback provider（有时间）
- Error handling
- structured logs

### 验收

- operator 无法 ingest
- manager 可以查看 audit
- admin 可以 ingest
- 每次 Agent run 都有 request_id
- tool call 有审计记录

---

## Day 5 — UI + Packaging + Interview Demo

### 目标

- Dashboard
- AI Workspace
- Knowledge page
- Docker Compose
- README
- ARCHITECTURE
- DEMO_SCRIPT
- 截图
- 最终 smoke test

### 验收

从干净环境：

```bash
git clone ...
cd hengguang-ai-platform-demo
cp .env.example .env
make/dev command
```

能够启动：

```text
API: http://localhost:8000
Web: http://localhost:3000
```

---

# 15. Demo Script

面试演示建议控制在 5–8 分钟。

## Step 1 — 30 秒：定位项目

说：

> 这是我针对贵公司的 AI 平台岗位做的一个技术原型。因为真实企业内部数据不能使用，所以知识库使用公开资料，ERP、安全等数据使用的是合成数据。
>
> 我的重点不是做一个聊天机器人，而是验证模型、知识、业务系统和 Agent 能否形成一个统一 AI Platform。

## Step 2 — 60 秒：展示 Dashboard

展示：

- 当前模型
- request count
- success rate
- latency

讲：

> 平台层先统一模型接入、日志和基础监控。

## Step 3 — 90 秒：RAG

输入：

> 恒光主要有哪些业务？

展示：

- 回答
- sources
- page / section

讲：

> 这里不是让模型凭记忆回答，而是先从企业公开资料中召回内容，再让模型生成带引用的回答。

## Step 4 — 90 秒：ERP Agent

输入：

> 最近 30 天原材料采购价格有什么变化？

展示：

```text
Agent
  -> ERP Tool
  -> SQL/aggregation
  -> LLM summary
```

强调：

> 模型不直接执行任意 SQL，而是只能调用白名单 Tool。

## Step 5 — 90 秒：Safety Agent

输入：

> 最近一个月哪个区域安全问题最多？

展示：

- tool call
- 结果
- 分析

再问：

> A车间最近安全问题为什么增加？相关安全制度有哪些？

展示多工具：

```text
Safety Tool
+
Knowledge Tool
+
LLM synthesis
```

## Step 6 — 60 秒：平台工程

展示：

- Model Gateway
- RBAC
- Audit Log
- Docker

最后说：

> 如果进入真实环境，我会把 ERP/OA/DCS 等真实接口通过 Tool/Connector 接入，但高风险生产控制仍然留在原有工业控制系统和人工审批链路中，AI 主要承担知识检索、数据分析和辅助决策。

---

# 16. 面试问题映射

项目做完后必须能回答：

### Q1. 为什么做 Model Gateway？

答案方向：

- 统一 API
- Provider 解耦
- 模型切换
- fallback
- 成本/效果评测

### Q2. 为什么不能直接让 Agent 执行任意 SQL？

答案方向：

- 安全
- 数据访问边界
- SQL injection / destructive query
- 可审计
- 白名单 Tool

### Q3. 化工企业为什么要 RAG？

答案方向：

- SOP
- 安全制度
- 设备文档
- 技术资料
- 研发资料
- 可追溯回答

### Q4. AI 能不能直接控制 DCS？

答案方向：

- 本 Demo 不做
- AI 做分析/辅助决策
- 关键控制保留在现有工业控制系统
- 人工确认 / 审批

### Q5. 如果模型回答错误怎么办？

答案方向：

- RAG
- source citation
- structured output
- evaluation set
- audit
- human-in-the-loop

### Q6. 怎么做模型选型？

答案方向：

建立 benchmark：

```text
准确率
中文能力
工具调用能力
延迟
token cost
私有化可行性
```

---

# 17. 验收标准

## P0 Acceptance

### Backend

- [ ] API 可启动
- [ ] `/health` 正常
- [ ] `/api/chat` 正常
- [ ] Model Gateway 有抽象
- [ ] Mock Provider 可运行
- [ ] Real Provider 可配置

### RAG

- [ ] 文档可 ingest
- [ ] 可检索
- [ ] 返回 metadata
- [ ] 回答带 source
- [ ] 不足信息时明确拒答/降级

### Agent

- [ ] Tool Registry
- [ ] Knowledge Tool
- [ ] ERP Tool
- [ ] Safety Tool
- [ ] Agent trace
- [ ] Tool 白名单
- [ ] 无任意 SQL

### Platform

- [ ] RBAC
- [ ] Audit Log
- [ ] request_id
- [ ] latency
- [ ] health check

### Frontend

- [ ] Dashboard
- [ ] Chat/Agent Workspace
- [ ] Knowledge

### Deployment

- [ ] Docker Compose
- [ ] `.env.example`
- [ ] fresh setup 可运行

### Documentation

- [ ] README
- [ ] ARCHITECTURE
- [ ] DEMO_SCRIPT
- [ ] 项目免责声明

---

# 18. Definition of Done

项目只有同时满足下面条件，才算完成：

```text
用户
  |
  v
Web UI
  |
  v
FastAPI
  |
  v
Agent Router
  |
  +----------------------+
  |                      |
  v                      v
Knowledge Tool      Business Tool
  |                   /       \
  v                  v         v
RAG               ERP       Safety
  |                  \         /
  +-------------------+-------+
                      |
                      v
                Model Gateway
                      |
                      v
                   LLM
                      |
                      v
             Answer + Sources
                      |
          +-----------+-----------+
          |                       |
          v                       v
      Audit Log               Metrics
```

并且：

1. 可以在本地跑起来。
2. 可以在 Docker 中跑起来。
3. 没有真实企业内部数据。
4. 没有真实生产控制能力。
5. 没有任何 secret 被提交到 Git。
6. 有测试。
7. 有完整 README。
8. 能在 5–8 分钟内完成演示。

---

# 19. Git Commit 建议

保持提交可读：

```text
feat: bootstrap fastapi platform
feat: add model gateway abstraction
feat: add rag ingestion and retrieval
feat: add synthetic erp and safety data
feat: add agent tool registry
feat: add rbac and audit log
feat: add dashboard and agent workspace
feat: add docker compose deployment

docs: add architecture and demo script

test: add gateway rag and agent integration tests
```

---

# 20. 最终 README 必须回答的问题

README 首页必须让陌生面试官 60 秒内看到：

1. **这是什么？**
2. **为什么做？**
3. **架构是什么？**
4. **能演示什么？**
5. **怎么运行？**
6. **如何与岗位 JD 对应？**
7. **哪些是公开数据，哪些是合成数据？**
8. **哪些能力没有做？为什么？**

首页建议结构：

```text
# Hengguang AI Platform Demo

One-line description

Screenshot / Architecture

Features

Architecture

Quick Start

Demo Scenarios

JD Mapping

Security / Safety Boundary

Roadmap

Disclaimer
```

---

# 21. 后续扩展（不要放进 3–5 天 MVP）

完成 MVP 后，如果要继续增强，再按以下顺序：

```text
Phase 2
├── real ERP connector
├── OA connector
├── MCP tools
├── model benchmark
├── prompt/version management
└── evaluation dataset

Phase 3
├── DCS historian integration
├── anomaly detection model
├── time-series analysis
├── equipment predictive maintenance
└── multi-agent workflow

Phase 4
├── enterprise SSO
├── secrets management
├── Kubernetes
├── distributed observability
└── multi-tenant platform
```

**不要在 MVP 阶段提前实现。**

---

# 22. 实现完成后的最终检查命令

后端：

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

启动：

```bash
uv run uvicorn app.main:app --reload
```

前端：

```bash
cd web
npm install
npm run build
```

Docker：

```bash
docker compose build
docker compose up -d
```

Smoke Test：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/models
```

然后人工验证四条 Demo Query：

```text
恒光主要有哪些业务？
最近30天原材料采购价格有什么变化？
最近一个月哪个区域安全问题最多？
A车间最近安全问题为什么增加？相关安全制度有哪些？
```

---

# 23. 给 coding agent 的最终执行指令

请严格按照本 `SPEC.md` 实现，不要自行扩大范围。

执行顺序：

```text
1. 读取 SPEC.md
2. 创建项目骨架
3. 实现 Day 1
4. 运行测试
5. 实现 Day 2
6. 运行测试
7. 实现 Day 3
8. 运行测试
9. 实现 Day 4
10. 运行测试
11. 实现 Day 5
12. 完成 README / ARCHITECTURE / DEMO_SCRIPT
13. 执行完整 smoke test
14. 最后输出变更总结、运行方式、测试结果、未完成 P1 项
```

### 输出报告格式

```text
## Implemented
- ...

## Tests
- ...

## Run
- ...

## Demo
- ...

## Remaining
- ...

## Notes
- ...
```

**如果遇到技术选型冲突，优先选择更简单、更容易在 5 天内完成、并且更容易解释给面试官的方案。**
