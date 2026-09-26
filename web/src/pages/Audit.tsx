/**
 * Audit — one request_id, the whole chain (Day 5 P0 #6, demo Step 6).
 *
 * `GET /api/audit` gives the paginated trail (API rows + one row per tool call);
 * clicking a row asks `GET /api/audit/{request_id}` for every row of that run, so
 * an interview can follow `agent.run → tool.call → tool.call …` for a single
 * question. Rows only ever contain the compact, sanitised summaries the backend
 * decided to store — no prompts, no document text, no credentials.
 *
 * The endpoint is `audit:read` (admin + manager). For operator the page shows the
 * backend's 403 as a Permission-denied state and stays functional.
 */

import { useCallback, useEffect, useState } from "react";

import { Badge, EmptyState, Loading, Panel, StatCard, StatusBadge } from "../components/Primitives";
import { FailureState } from "../components/States";
import { handoffRequest, takeHandoffRequest } from "../app/handoff";
import { useDemoUser } from "../app/DemoUserContext";
import { useAsync, useAutoRefresh } from "../hooks/useAsync";
import { api, asFailure } from "../services/api";
import type { ApiFailure, AuditEntry, AuditListResponse } from "../types";

const PAGE_SIZE = 20;

interface Filters {
  page: number;
  status: string;
  action: string;
  tool: string;
  request_id: string;
}

const EMPTY_FILTERS: Filters = { page: 1, status: "", action: "", tool: "", request_id: "" };

function summarize(entry: AuditEntry): string {
  const parts = Object.entries(entry.input_summary)
    .filter(([, value]) => value !== "" && value !== null)
    .map(([key, value]) => `${key}=${value}`);
  return parts.join(" · ");
}

export function Audit() {
  const { revision, role } = useDemoUser();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [selectedRid, setSelectedRid] = useState<string | null>(null);
  const [detail, setDetail] = useState<AuditListResponse | null>(null);
  const [detailError, setDetailError] = useState<ApiFailure | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // A run started from the playground can hand its request id over to this page.
  useEffect(() => {
    const handed = takeHandoffRequest();
    if (handed) {
      setFilters({ ...EMPTY_FILTERS, request_id: handed });
      void openTrace(handed);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = useCallback(
    (signal: AbortSignal) =>
      api.audit(
        {
          page: filters.page,
          page_size: PAGE_SIZE,
          status: filters.status || undefined,
          action: filters.action || undefined,
          tool: filters.tool || undefined,
          request_id: filters.request_id || undefined,
        },
        signal,
      ),
    [filters],
  );
  const list = useAsync(load, [revision, filters]);
  useAutoRefresh(list.reload, 20_000, !list.error);

  async function openTrace(requestId: string) {
    setSelectedRid(requestId);
    setLoadingDetail(true);
    setDetailError(null);
    try {
      setDetail(await api.auditTrace(requestId));
    } catch (error) {
      setDetail(null);
      setDetailError(asFailure(error));
    } finally {
      setLoadingDetail(false);
    }
  }

  const items = list.data?.items ?? [];
  const total = list.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const toolRows = items.filter((entry) => entry.action === "tool.call");
  const deniedRows = items.filter((entry) => entry.status === "denied");

  return (
    <div className="stack">
      <div className="grid-cards">
        <StatCard label="Audit rows (total)" value={total} foot="GET /api/audit · audit:read" small />
        <StatCard label="Page" value={`${filters.page} / ${pages}`} foot={`page_size=${PAGE_SIZE}`} small />
        <StatCard label="tool.call rows on page" value={toolRows.length} foot="每个工具调用一行" small />
        <StatCard
          label="denied on page"
          value={
            <span style={{ color: deniedRows.length ? "var(--err)" : undefined }}>
              {deniedRows.length}
            </span>
          }
          foot="权限拒绝同样落审计"
          small
        />
      </div>

      <Panel
        title="Audit trail"
        sub={`viewer: ${list.data?.viewer ? `${list.data.viewer.username} (${list.data.viewer.role})` : role}`}
        actions={
          <>
            <select
              value={filters.status}
              onChange={(event) => setFilters({ ...filters, status: event.target.value, page: 1 })}
            >
              <option value="">status: all</option>
              <option value="success">success</option>
              <option value="denied">denied</option>
              <option value="error">error</option>
            </select>
            <select
              value={filters.action}
              onChange={(event) => setFilters({ ...filters, action: event.target.value, page: 1 })}
            >
              <option value="">action: all</option>
              {["agent.run", "tool.call", "chat.complete", "knowledge.search", "knowledge.ingest", "models.list"].map(
                (action) => (
                  <option key={action} value={action}>
                    {action}
                  </option>
                ),
              )}
            </select>
            <select
              value={filters.tool}
              onChange={(event) => setFilters({ ...filters, tool: event.target.value, page: 1 })}
            >
              <option value="">tool: all</option>
              {[
                "knowledge_search",
                "document_lookup",
                "erp_purchase_analysis",
                "safety_incident_analysis",
              ].map((tool) => (
                <option key={tool} value={tool}>
                  {tool}
                </option>
              ))}
            </select>
            <input
              style={{ width: 220 }}
              placeholder="request_id 过滤"
              value={filters.request_id}
              onChange={(event) =>
                setFilters({ ...filters, request_id: event.target.value.trim(), page: 1 })
              }
            />
            <button
              className="btn small"
              type="button"
              onClick={() => setFilters(EMPTY_FILTERS)}
              title="清除全部过滤条件"
            >
              清除
            </button>
            <button className="btn small" type="button" onClick={list.reload}>
              刷新
            </button>
          </>
        }
      >
        {list.error ? (
          list.error.denied ? (
            <FailureState
              failure={list.error}
              compact
              onRetry={list.reload}
              hint={
                <>
                  审计日志需要 <span className="mono">audit:read</span>（admin / manager）。
                  当前角色 <b className="mono">{role}</b> 被后端拒绝 —— 前端没有绕过它的方法。
                  切到 Manager 或 Admin 再看同一份数据。
                </>
              }
            />
          ) : (
            <FailureState failure={list.error} compact onRetry={list.reload} />
          )
        ) : list.loading && !list.data ? (
          <Loading text="读取审计日志…" />
        ) : items.length === 0 ? (
          <EmptyState
            title="没有匹配的审计记录"
            hint="先在 Agent Playground 跑一次提问，或清除过滤条件。"
          />
        ) : (
          <div className="scroll-x">
            <table className="data">
              <thead>
                <tr>
                  <th>time</th>
                  <th>user</th>
                  <th>action</th>
                  <th>tool</th>
                  <th>status</th>
                  <th className="num">latency</th>
                  <th>request_id</th>
                </tr>
              </thead>
              <tbody>
                {items.map((entry) => (
                  <tr
                    key={entry.id}
                    className={`clickable ${entry.request_id === selectedRid ? "selected" : ""}`}
                    onClick={() => void openTrace(entry.request_id)}
                  >
                    <td className="tag">{entry.created_at}</td>
                    <td>
                      {entry.username}
                      <span className="tag"> · {entry.role}</span>
                    </td>
                    <td className="tag">
                      {entry.action}
                      {entry.endpoint ? ` · ${entry.endpoint}` : ""}
                    </td>
                    <td className="tag">{entry.tool ?? "—"}</td>
                    <td>
                      <StatusBadge status={entry.status} />
                    </td>
                    <td className="num">{entry.latency_ms ?? 0} ms</td>
                    <td className="tag mono">{entry.request_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="toolbar" style={{ marginTop: 10 }}>
              <button
                className="btn small"
                type="button"
                disabled={filters.page <= 1}
                onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
              >
                ← 上一页
              </button>
              <span className="hint">
                第 {filters.page} / {pages} 页 · 共 {total} 行 · 点击任意行查看该 request_id 的完整链路
              </span>
              <button
                className="btn small"
                type="button"
                disabled={filters.page >= pages}
                onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
              >
                下一页 →
              </button>
            </div>
          </div>
        )}
      </Panel>

      <Panel
        title={selectedRid ? `Request trace · ${selectedRid}` : "Request trace"}
        sub="GET /api/audit/{request_id}"
        actions={
          selectedRid ? (
            <>
              <Badge tone="info">{detail?.items.length ?? 0} rows</Badge>
              <button
                className="btn small"
                type="button"
                onClick={() => {
                  handoffRequest(selectedRid);
                  setFilters({ ...EMPTY_FILTERS, request_id: selectedRid });
                }}
              >
                用该 request_id 过滤列表
              </button>
            </>
          ) : undefined
        }
      >
        {!selectedRid ? (
          <p className="hint">选择左侧任意一行，查看这一轮从 API → Agent → Tool → Audit 的全部记录。</p>
        ) : loadingDetail ? (
          <Loading text="读取该请求的链路…" />
        ) : detailError ? (
          <FailureState failure={detailError} compact onRetry={() => void openTrace(selectedRid)} />
        ) : (
          <div className="stack">
            <div className="row">
              <Badge tone="ok">query_request_id {detail?.query_request_id}</Badge>
              <Badge>rows {detail?.total ?? 0}</Badge>
              <Badge>{detail?.items[0]?.username ?? "—"} · {detail?.items[0]?.role ?? "—"}</Badge>
            </div>
            <div className="timeline">
              {(detail?.items ?? []).map((entry, index) => (
                <div className="tl-item" key={entry.id}>
                  <div className="tl-rail">
                    <span className={`tl-index ${entry.action === "tool.call" ? "tool" : ""}`}>
                      {index + 1}
                    </span>
                  </div>
                  <div className="tl-body">
                    <div className="tl-title">
                      <Badge tone={entry.action === "tool.call" ? "info" : "neutral"}>
                        {entry.action}
                      </Badge>
                      <span className="mono">{entry.tool ?? entry.endpoint ?? "—"}</span>
                      <StatusBadge status={entry.status} />
                      <Badge>{entry.latency_ms ?? 0} ms</Badge>
                      {entry.model && <span className="tag">model={entry.model}</span>}
                      {entry.mode && <span className="tag">mode={entry.mode}</span>}
                    </div>
                    <div className="tl-sub">{summarize(entry) || "（该操作未存储额外摘要）"}</div>
                  </div>
                </div>
              ))}
            </div>
            <p className="hint">
              审计只存参数摘要与统计（operation / days / limit / status / latency），不记录 prompt、
              文档全文、token 或 API Key。
            </p>
          </div>
        )}
      </Panel>
    </div>
  );
}
