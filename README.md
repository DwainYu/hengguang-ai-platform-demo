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

项目骨架已初始化（目录结构、uv 项目、FastAPI `/health`、前端 3 页占位、Docker Compose）。
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

## Demo Scenarios（目标）

| 场景 | 输入 | 走通 |
|---|---|---|
| 企业知识 RAG | 恒光主要有哪些业务？ | knowledge_search |
| ERP 分析 | 最近30天原材料采购价格有什么变化？ | erp_purchase_analysis |
| 安全分析 | 最近一个月哪个区域安全问题最多？ | safety_incident_analysis |
| 综合分析 | A车间最近安全问题为什么增加？相关制度有哪些？ | Safety + Knowledge + LLM |

## 数据边界

- 公开数据：`data/documents/`（公开公司简介、公开年报/新闻）
- 合成数据：`data/synthetic/`（ERP 采购、安全事件、设备维护）
- 不接入真实 ERP/OA/DCS，不做真实生产控制。

## 运行环境要求

- Python 3.11+（uv 管理）
- Node.js 18+（前端）
- Docker / Docker Compose（可选部署）
