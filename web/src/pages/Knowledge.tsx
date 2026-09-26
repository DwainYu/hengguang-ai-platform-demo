/**
 * Knowledge — the Day-2 RAG surface as a page (Day 5 P0 #4, #7, #8).
 *
 * Documents / chunk statistics come from `GET /api/knowledge/documents`, the
 * search panel is `POST /api/knowledge/search` (retrieval + citations + the
 * generated answer), and the rebuild button is `POST /api/knowledge/ingest`.
 * No retrieval logic is re-implemented in the browser.
 *
 * Ingest is `knowledge:ingest` = admin only. For any other role the button is
 * disabled *and* the backend still answers 403 if the request is forced — the UI
 * never pretends to be the security boundary.
 */

import { useCallback, useState } from "react";

import { Badge, EmptyState, Loading, Panel, StatCard, StatusBadge } from "../components/Primitives";
import { FailureState, isKnowledgeNotReady } from "../components/States";
import { useDemoUser } from "../app/DemoUserContext";
import { useAsync } from "../hooks/useAsync";
import { api, asFailure } from "../services/api";
import type { ApiFailure, IngestResponse, SearchResponse } from "../types";

const SUGGESTED = [
  "恒光主要有哪些业务？",
  "恒光的氯碱产品有哪些？",
  "2025 年营业收入是多少？",
  "公司安全生产制度有哪些要求？",
];

export function Knowledge() {
  const { revision, role } = useDemoUser();
  const [query, setQuery] = useState(SUGGESTED[0]);
  const [topK, setTopK] = useState(5);
  const [answer, setAnswer] = useState(true);
  const [search, setSearch] = useState<SearchResponse | null>(null);
  const [searchError, setSearchError] = useState<ApiFailure | null>(null);
  const [searching, setSearching] = useState(false);
  const [ingest, setIngest] = useState<IngestResponse | null>(null);
  const [ingestError, setIngestError] = useState<ApiFailure | null>(null);
  const [ingesting, setIngesting] = useState(false);

  const loadDocs = useCallback((signal: AbortSignal) => api.knowledgeDocuments(signal), []);
  const docs = useAsync(loadDocs, [revision, ingest?.chunks ?? 0]);

  const runSearch = useCallback(async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    try {
      setSearch(await api.knowledgeSearch({ query: query.trim(), top_k: topK, include_answer: answer }));
    } catch (error) {
      setSearch(null);
      setSearchError(asFailure(error));
    } finally {
      setSearching(false);
    }
  }, [answer, query, topK]);

  const { reload: reloadDocs } = docs;
  const runIngest = useCallback(async () => {
    setIngesting(true);
    setIngestError(null);
    try {
      setIngest(await api.knowledgeIngest({ rebuild: true }));
      reloadDocs();
    } catch (error) {
      setIngestError(asFailure(error));
    } finally {
      setIngesting(false);
    }
  }, [reloadDocs]);

  const isAdmin = role === "admin";

  return (
    <div className="stack">
      <div className="grid-cards">
        <StatCard
          label="Documents"
          value={docs.data?.total_documents ?? (docs.loading ? "…" : 0)}
          foot="GET /api/knowledge/documents"
        />
        <StatCard
          label="Chunks"
          value={docs.data?.total_chunks ?? (docs.loading ? "…" : 0)}
          foot={`avg ${docs.data && docs.data.total_documents ? Math.round(docs.data.total_chunks / docs.data.total_documents) : 0} chunks / doc`}
        />
        <StatCard
          label="Collection Status"
          value={
            docs.error ? (
              <Badge tone="warn">{docs.error.code}</Badge>
            ) : docs.data && docs.data.total_chunks > 0 ? (
              "ready"
            ) : (
              "not ready"
            )
          }
          foot={
            docs.error
              ? docs.error.message
              : `Chroma collection · provider 由 EMBEDDING_PROVIDER 决定（默认离线 mock）`
          }
        />
        <StatCard
          label="Last Ingest"
          value={ingest ? `${ingest.documents} docs` : "—"}
          small
          foot={
            ingest
              ? `${ingest.chunks} chunks · ${ingest.status} · request_id ${ingest.request_id}`
              : `POST /api/knowledge/ingest · 仅 admin`
          }
        />
      </div>

      <div className="split">
        <div className="stack">
          <Panel
            title="Search（带引用的检索）"
            sub="POST /api/knowledge/search"
            actions={<Badge tone="info">role: {role}</Badge>}
          >
            <div className="stack">
              <div className="toolbar">
                {SUGGESTED.map((item) => (
                  <button
                    key={item}
                    className="btn chip"
                    type="button"
                    onClick={() => setQuery(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  style={{ flex: 1 }}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void runSearch();
                  }}
                  placeholder="输入检索问题"
                />
                <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  top_k
                  <select value={topK} onChange={(event) => setTopK(Number(event.target.value))}>
                    {[3, 5, 8, 10].map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={answer}
                    onChange={(event) => setAnswer(event.target.checked)}
                    style={{ width: 14 }}
                  />
                  answer
                </label>
                <button className="btn primary" type="button" disabled={searching} onClick={() => void runSearch()}>
                  {searching ? <span className="spinner" /> : null} Search
                </button>
              </div>

              {searchError && (
                <FailureState
                  failure={searchError}
                  compact
                  onRetry={() => void runSearch()}
                  hint={
                    isKnowledgeNotReady(searchError)
                      ? "Knowledge base is not ready. 请让 admin 执行下方 Ingest / Rebuild。"
                      : undefined
                  }
                />
              )}
              {search && (
                <div className="stack">
                  <div className="row">
                    <Badge tone="ok">{search.count} hits</Badge>
                    <Badge>{search.latency_ms} ms</Badge>
                    <Badge>{search.provider} / {search.model}</Badge>
                    <span className="tag">request_id {search.request_id}</span>
                  </div>
                  {search.answer && (
                    <div className="answer-box">
                      <div className="who mono" style={{ color: "var(--text-faint)", marginBottom: 6 }}>
                        ANSWER · Model Gateway {answer ? "" : "未启用"}
                      </div>
                      {search.answer}
                    </div>
                  )}
                  {!answer && <p className="hint">已关闭生成回答：只返回召回结果与 citation。</p>}
                </div>
              )}
              {!search && !searchError && !searching && (
                <p className="hint">
                  检索链路：query → embedding → Chroma 向量召回 + 词面融合 → top_k chunks → 编号 context →
                  Model Gateway 生成带 [n] 引用的回答。
                </p>
              )}
            </div>
          </Panel>

          <Panel
            title="Ingest / Rebuild"
            sub="POST /api/knowledge/ingest · knowledge:ingest = admin only"
            actions={
              <button
                className="btn"
                type="button"
                disabled={!isAdmin || ingesting}
                onClick={() => void runIngest()}
                title={isAdmin ? "清空集合并重新导入 data/documents/" : "需要 admin 角色"}
              >
                {ingesting ? <span className="spinner" /> : null} Rebuild / Ingest Knowledge
              </button>
            }
          >
            <div className="stack">
              {!isAdmin && (
                <div className="state denied">
                  <h3>
                    <Badge tone="warn">Permission denied</Badge> 当前角色 {role}
                  </h3>
                  <p>
                    重建知识库需要 <span className="mono">knowledge:ingest</span>（admin）。前端禁用按钮只是
                    UX：即使用手工请求，后端也会返回 403。
                  </p>
                </div>
              )}
              {ingestError && <FailureState failure={ingestError} compact onRetry={() => void runIngest()} />}
              {ingest && (
                <div className="row">
                  <StatusBadge status={ingest.status} />
                  <span className="tag">documents={ingest.documents}</span>
                  <span className="tag">chunks={ingest.chunks}</span>
                  <span className="tag">skipped={ingest.skipped.length}</span>
                  <span className="tag">errors={ingest.errors.length}</span>
                  <span className="tag">request_id={ingest.request_id}</span>
                </div>
              )}
              <p className="hint">
                只导入 <code>data/documents/</code> 的公开资料（公司公开简介、2025 年报、2026 半年报、
                产品与产能、公开新闻）。本次演示不提供文件上传。
              </p>
            </div>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Retrieved chunks" sub={search ? `query: ${search.query}` : "等待检索"}>
            {searching ? (
              <Loading text="检索中…" />
            ) : search ? (
              search.results.length === 0 ? (
                <EmptyState title="没有召回任何 chunk" hint="换个说法，或降低 top_k 门槛后重试。" />
              ) : (
                <div className="stack">
                  {search.results.map((result, index) => (
                    <div className="source" key={result.chunk_id}>
                      <div className="head">
                        <Badge tone="info">[{index + 1}]</Badge>
                        <span className="cite">{result.citation || result.title}</span>
                      </div>
                      <div className="kv">
                        <span>document_id={result.document_id}</span>
                        {result.section && <span>section={result.section}</span>}
                        {result.page !== null && <span>page={result.page}</span>}
                        <span>score={result.score.toFixed(4)}</span>
                        <span>position={result.position}</span>
                        <span>chars={result.content.length}</span>
                        <span>source={result.source}</span>
                      </div>
                      <div className="snippet">{result.content}</div>
                      {result.url && (
                        <a className="link" href={result.url} target="_blank" rel="noreferrer">
                          {result.url}
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )
            ) : (
              <p className="hint">执行一次检索后，这里显示每个 chunk 的 title / section / page / score 与 citation。</p>
            )}
          </Panel>

          <Panel title="Documents" sub={docs.data ? `${docs.data.total_documents} 篇公开资料` : "—"}>
            {docs.error ? (
              <FailureState failure={docs.error} compact onRetry={docs.reload} />
            ) : docs.loading && !docs.data ? (
              <Loading text="读取文档清单…" />
            ) : (
              <div className="scroll-x">
                <table className="data">
                  <thead>
                    <tr>
                      <th>title</th>
                      <th className="num">chunks</th>
                      <th className="num">chars</th>
                      <th>published</th>
                      <th>sections</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(docs.data?.documents ?? []).map((document) => (
                      <tr key={document.document_id}>
                        <td>
                          <div>{document.title}</div>
                          <div className="tag">{document.document_id}</div>
                          {document.url && (
                            <a className="link" href={document.url} target="_blank" rel="noreferrer">
                              {document.url}
                            </a>
                          )}
                        </td>
                        <td className="num">{document.chunks}</td>
                        <td className="num">{document.chars}</td>
                        <td className="tag">{document.published_at || "—"}</td>
                        <td className="hint">{document.sections.join(" / ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
