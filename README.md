# Hengguang AI Platform Demo

面向「湖南恒光科技股份有限公司 AI 平台工程师」岗位的 3–5 天求职技术 Demo：
一个可运行、可演示、可 Docker 部署的最小企业 AI 平台原型，覆盖 Model Gateway、RAG、Agent、
RBAC、审计与监控。

**声明**：本项目仅用于技术演示和求职交流。知识库只用公开资料，ERP / 安全 / 设备数据全部为
合成数据（synthetic data），不接入恒光内部系统，不使用任何内部数据、账号或密钥。

## 这是什么 / 为什么做

- 模拟化工制造企业在已有 OA/ERP/DCS 基础上引入统一 AI 能力层。
- 重点不是聊天机器人，而是验证「模型 + 知识 + 业务系统 + Agent」能否形成一个统一 AI 平台。

## 架构

```text
Web UI -> FastAPI -> Agent Router
                  |  RAG (Chroma)
                  |  Model Gateway -> LLM (mock / OpenAI-compatible)
                  |  Whitelisted Tools -> SQLite (synthetic ERP / Safety)
                  v
           Answer + Sources -> Audit Log / Metrics
```

详见 [ARCHITECTURE.md](./ARCHITECTURE.md) 与 [SPEC.md](./SPEC.md)。

## 当前状态

✅ **Day 1 完成**：Model Gateway + MockProvider + `/api/chat` + pytest 全通过

- Model Gateway 抽象层（`app/gateway/`）
- MockProvider 无需 API Key 即可运行
- OpenAI-compatible Provider 预留扩展（DeepSeek/Qwen/Ollama）
- `/health`、`/api/models`、`/api/chat` 三个核心端点

✅ **Day 2 完成**：RAG 知识库（ingest → chunk → embedding → Chroma → 检索 → citation）

- 文档提取（`app/rag/extractor.py`）：Markdown / TXT / PDF（pypdf 按页提取）
- Markdown 感知 chunker（`app/rag/chunker.py`）：按 heading 切分，800–1200 字、
  overlap 100–200，超长章节按句子边界滑窗
- 可替换 EmbeddingProvider（`app/embeddings/`）：默认离线 mock（hash n-gram，无需 API Key），
  可切 OpenAI-compatible `/embeddings`
- Chroma 持久化向量库（`app/rag/store.py`），混合检索（向量 + 词面重合，`app/rag/retriever.py`）
- RAG 回答（`app/rag/pipeline.py`）：召回 → 编号 context → Model Gateway 生成带 `[n]` 引用的回答，
  找不到依据时明确说明「知识库没有足够信息」
- `/api/knowledge/ingest`、`/api/knowledge/documents`、`/api/knowledge/search`
- 知识库只含公开资料（公司公开简介、2025 年报、2026 半年报、产品/产能、公开新闻），
  每篇文档带 document_id / title / source / url / published_at metadata
- 单元/集成测试 93 个全部通过（零 API Key）

按 SPEC 第 14 节的 5 天计划逐步实现：Day 1 Platform Skeleton → Day 5 UI + Packaging。

## Quick Start

```bash
# Backend (default: mock providers, no API key needed)
uv sync
uv run uvicorn app.main:app --reload   # http://localhost:8000

# Tests
uv run pytest

# Frontend
cd web && npm install && npm run dev    # http://localhost:5173 (dev)

# Docker
cp .env.example .env
docker compose up -d                    # API :8000, Web :3000
```

首次启动后需要把公开资料导入知识库（写入 `CHROMA_PATH`）：

```bash
curl -X POST http://localhost:8000/api/knowledge/ingest -H 'Content-Type: application/json' -d '{}'
# {"documents":6,"chunks":45,"status":"completed"}
```

# Frontend
cd web && npm install && npm run dev    # http://localhost:5173 (dev)

# Docker
cp .env.example .env
docker compose up -d                    # API :8000, Web :3000
```

## API 示例

```bash
# 健康检查
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}

# 模型列表
curl http://localhost:8000/api/models
# {"models":[{"provider":"mock","model":"mock-model","enabled":true}]}

# 聊天（自动使用 MockProvider）
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "你好"}'
# {"request_id":"req_xxx","answer":"你好！我是恒光 AI 平台的模拟助手...","mode":"auto","model":"mock-model","provider":"mock","latency_ms":0,"sources":[],"tool_calls":[]}

# Demo 场景查询
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "恒光主要有哪些业务？"}'

curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "最近30天原材料采购价格有什么变化？"}'

curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "最近一个月哪个区域安全问题最多？"}'
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "最近一个月哪个区域安全问题最多？"}'

# 知识库 ingest（首次启动后执行一次；RBAC（admin）在 Day 4 接入）
curl -X POST http://localhost:8000/api/knowledge/ingest \
  -H 'Content-Type: application/json' -d '{"path": "data/documents"}'
# {"documents":6,"chunks":45,"status":"completed","skipped":[],"errors":[]}

# 知识库文档列表 + chunk 统计
curl http://localhost:8000/api/knowledge/documents

# 知识库检索：Top-K chunks + metadata + citation + 带引用的回答
curl -X POST http://localhost:8000/api/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "恒光主要有哪些业务？", "top_k": 3}'
# {"query":"...","count":3,
#  "results":[{"document_id":"hengguang-public-profile","title":"湖南恒光科技股份有限公司公开简介",
#              "section":"主营业务","content":"## 主营业务 ...","score":0.24,"citation":"... · 主营业务"}],
#  "citations":[{"index":1,"document_id":"...","title":"...","section":"主营业务"}],
#  "answer":"根据知识库检索到的 3 条资料... [1]","model":"mock-model","provider":"mock","latency_ms":3}
```

## Demo Scenarios

| 场景 | 输入 | 走通 | 状态 |
|---|---|---|---|
| 企业知识 RAG | 恒光主要有哪些业务？ | `POST /api/knowledge/search`（Day 3 起走 knowledge_search 工具） | ✅ Day 2 |
| ERP 分析 | 最近30天原材料采购价格有什么变化？ | erp_purchase_analysis | Day 3 |
| 安全分析 | 最近一个月哪个区域安全问题最多？ | safety_incident_analysis | Day 3 |
| 综合分析 | A车间最近安全问题为什么增加？相关制度有哪些？ | Safety + Knowledge + LLM | Day 3 |

> `/api/chat` 仍走 Model Gateway（Day 1 行为）；Day 3 通过 Agent Router 接入 knowledge_search 等
> 工具后，chat 会自动带上 sources。

## 数据边界

- 公开数据：`data/documents/`（公开公司简介、公开年报/新闻）
- 合成数据：`data/synthetic/`（ERP 采购、安全事件、设备维护）
- 不接入真实 ERP/OA/DCS，不做真实生产控制。

## 运行环境要求

- Python 3.11+（uv 管理）
- Node.js 18+（前端）
- Docker / Docker Compose（可选部署）
