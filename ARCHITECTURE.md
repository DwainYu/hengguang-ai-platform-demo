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
| 业务数据库 | `app/db/` + `data/synthetic/` | SQLite + 合成数据。查询全部使用参数化 SQL / 固定 query function，禁止 LLM 生成任意 SQL。 |
| RBAC | `app/auth/` | 简单 Bearer Token，三角色：admin / manager / operator。 |
| 审计 / 指标 | `app/observability/` | request_id、user、endpoint、model、mode、tool、latency_ms、status；审计不记录 API Key 与敏感文档全文。 |

## 安全边界

- 高风险业务只做分析 / 辅助决策，不接真实 DCS，不做工业控制。
- 知识库只允许公开资料（SPEC 6.1）；`data/documents/` 每篇文档带 YAML front matter
  （document_id / title / source / url / published_at），README.md 与不支持的类型跳过。
- 不提交任何 secret 到 Git；`.env` 默认全部 mock，无需 key 即可运行测试与 UI。
