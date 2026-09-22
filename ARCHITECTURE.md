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
| Embedding | `app/embeddings/` | 可替换 `EmbeddingProvider` 抽象，默认 mock，支持 OpenAI-compatible / Ollama。 |
| RAG | `app/rag/` | Markdown chunk（800–1200 字，overlap 100–200），Chroma persistent client，top_k=5，检索结果必须带 document_id / title / page / section / source / score。 |
| Agent | `app/agent/` | 规则路由 baseline + LLM 工具选择增强（失败必须回退规则路由）。工具白名单：`knowledge_search`、`erp_purchase_analysis`、`safety_incident_analysis`（+ 可选 `equipment_maintenance_lookup`）。 |
| 业务数据库 | `app/db/` + `data/synthetic/` | SQLite + 合成数据。查询全部使用参数化 SQL / 固定 query function，禁止 LLM 生成任意 SQL。 |
| RBAC | `app/auth/` | 简单 Bearer Token，三角色：admin / manager / operator。 |
| 审计 / 指标 | `app/observability/` | request_id、user、endpoint、model、mode、tool、latency_ms、status；审计不记录 API Key 与敏感文档全文。 |

## 安全边界

- 高风险业务只做分析 / 辅助决策，不接真实 DCS，不做工业控制。
- 不提交任何 secret 到 Git；`.env` 默认全部 mock，无需 key 即可运行测试与 UI。
