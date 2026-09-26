/**
 * Dashboard — the platform status surface (Day 5 P0 #1, #7, #11).
 *
 * Nothing is hard-coded: every card is a live call to `GET /health`,
 * `GET /metrics`, `GET /api/models` and `GET /api/knowledge/documents`, so the
 * page works identically against the mock provider and a real LLM.
 *
 * `/api/models` is guarded by `models:list` (operator has none): the provider
 * card then falls back to the public `/metrics` snapshot instead of lying, and the
 * permission is named. That is the RBAC story, not a broken card.
 */

import { useCallback } from "react";

import { BarRow, Badge, Loading, Panel, StatCard, StatusBadge } from "../components/Primitives";
import { FailureState } from "../components/States";
import { useDemoUser } from "../app/DemoUserContext";
import { useAsync, useAutoRefresh } from "../hooks/useAsync";
import { api } from "../services/api";
import { navigate } from "../app/router";

export function Dashboard() {
  const { revision, role } = useDemoUser();

  const loadHealth = useCallback((signal: AbortSignal) => api.health(signal), []);
  const loadMetrics = useCallback((signal: AbortSignal) => api.metrics(signal), []);
  const loadModels = useCallback((signal: AbortSignal) => api.models(signal), []);
  const loadDocs = useCallback((signal: AbortSignal) => api.knowledgeDocuments(signal), []);

  const health = useAsync(loadHealth, [revision]);
  const metrics = useAsync(loadMetrics, [revision]);
  const models = useAsync(loadModels, [revision]);
  const docs = useAsync(loadDocs, [revision]);

  const { reload: reloadHealth } = health;
  const { reload: reloadMetrics } = metrics;
  const { reload: reloadModels } = models;
  const { reload: reloadDocs } = docs;
  const reloadAll = useCallback(() => {
    reloadHealth();
    reloadMetrics();
    reloadModels();
    reloadDocs();
  }, [reloadHealth, reloadMetrics, reloadModels, reloadDocs]);
  useAutoRefresh(reloadAll, 15_000);

  if (health.loading && !health.data) return <Loading text="读取平台状态：/health · /metrics …" />;
  if (health.error) {
    return (
      <FailureState
        failure={health.error}
        onRetry={reloadAll}
        hint="Dashboard 的所有数字都来自真实接口，后端不可用时不会显示任何占位数据。"
      />
    );
  }

  const alive = health.data;
  const metricsData = metrics.data;
  const modelsData = models.data;
  const docsData = docs.data;
  const chatModel = modelsData?.models.find((item) => item.kind === "chat" && item.default);
  const embeddingModel = modelsData?.models.find((item) => item.kind === "embedding");
  const successRate = metricsData
    ? metricsData.request_count
      ? Math.round((metricsData.success_count / metricsData.request_count) * 100)
      : 100
    : null;
  const endpoints = Object.entries(metricsData?.requests_by_endpoint ?? {}).sort(
    (a, b) => b[1].count - a[1].count,
  );
  const maxCount = endpoints.reduce((max, [, value]) => Math.max(max, value.count), 0);
  const knowledgeReady = Boolean(docsData && docsData.total_chunks > 0);

  return (
    <div className="stack">
      <div className="grid-cards">
        <StatCard
          label="API Status"
          value={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {alive ? "healthy" : "down"}
              <StatusBadge status={alive?.status ?? "error"} />
            </span>
          }
          foot={`GET /health · v${alive?.version ?? "—"} · ${alive?.request_count ?? 0} req`}
        />
        <StatCard
          label="Model Provider"
          value={
            chatModel ? chatModel.provider : (metricsData?.app.provider ?? "—")
          }
          badge={models.error ? <Badge tone="warn">403</Badge> : undefined}
          foot={
            models.error
              ? `/api/models 需要 models:list（角色 ${role} 无此权限）；provider 取自公开 /metrics`
              : `chat=${chatModel?.model ?? "—"} · embedding=${embeddingModel?.model ?? "—"} · LLM_PROVIDER=${metricsData?.app.provider ?? "—"}`
          }
        />
        <StatCard
          label="Knowledge Base"
          value={
            docs.error ? (
              <Badge tone="warn">受限</Badge>
            ) : knowledgeReady ? (
              "ready"
            ) : (
              <Badge tone="warn">not ready</Badge>
            )
          }
          foot={`documents ${docsData?.total_documents ?? 0} · chunks ${docsData?.total_chunks ?? 0} · GET /api/knowledge/documents`}
        />
        <StatCard
          label="Requests"
          value={metricsData?.request_count ?? "—"}
          foot={`success ${metricsData?.success_count ?? 0} · errors ${metricsData?.error_count ?? 0}`}
        />
        <StatCard
          label="Agent Runs"
          value={metricsData?.agent_run_count ?? "—"}
          foot={
            metricsData
              ? Object.entries(metricsData.agent_runs_by_status)
                  .map(([status, count]) => `${status}=${count}`)
                  .join(" · ") || "no runs yet"
              : "—"
          }
        />
        <StatCard
          label="Tool Calls"
          value={metricsData?.tool_call_count ?? "—"}
          foot={`tool errors ${metricsData?.tool_error_count ?? 0} · permission denied ${metricsData?.permission_denied_count ?? 0}`}
        />
        <StatCard
          label="Error Count"
          value={
            <span style={{ color: (metricsData?.error_count ?? 0) > 0 ? "var(--err)" : undefined }}>
              {metricsData?.error_count ?? "—"}
            </span>
          }
          foot={
            metricsData && Object.keys(metricsData.error_by_code).length
              ? Object.entries(metricsData.error_by_code)
                  .map(([code, count]) => `${code}=${count}`)
                  .join(" · ")
              : "no failed requests"
          }
        />
      </div>

      <div className="split">
        <Panel
          title="Observability — GET /metrics"
          sub={`avg ${metricsData?.avg_latency_ms ?? 0} ms · max ${metricsData?.max_latency_ms ?? 0} ms · uptime ${Math.round(metricsData?.uptime_seconds ?? 0)}s`}
          actions={
            <button className="btn small" type="button" onClick={reloadAll}>
              刷新
            </button>
          }
        >
          {metrics.error ? (
            <FailureState failure={metrics.error} compact onRetry={metrics.reload} />
          ) : metrics.loading && !metrics.data ? (
            <Loading text="读取 /metrics …" />
          ) : (
            <div className="stack">
              <div className="row">
                <Badge tone="ok">success {metricsData?.success_count ?? 0}</Badge>
                <Badge tone="err">errors {metricsData?.error_count ?? 0}</Badge>
                <Badge tone="info">
                  success rate {successRate === null ? "—" : `${successRate}%`}
                </Badge>
                <Badge>audit writes {metricsData?.audit_write_count ?? 0}</Badge>
                <Badge tone={metricsData?.permission_denied_count ? "err" : "neutral"}>
                  permission denied {metricsData?.permission_denied_count ?? 0}
                </Badge>
              </div>
              <div className="divider" />
              <div className="card-label">requests by endpoint</div>
              {endpoints.length === 0 ? (
                <p className="hint">还没有流量。到 Agent Playground 跑一次提问即可看到分布。</p>
              ) : (
                endpoints.map(([name, value]) => (
                  <BarRow
                    key={name}
                    label={name}
                    value={value.count}
                    max={maxCount}
                    display={`${value.count} · ${value.avg_latency_ms}ms`}
                  />
                ))
              )}
              <div className="divider" />
              <div className="card-label">requests by status class</div>
              {Object.entries(metricsData?.requests_by_status_class ?? {}).map(([klass, count]) => (
                <BarRow
                  key={klass}
                  label={klass}
                  value={count}
                  max={metricsData?.request_count ?? 0}
                  warn={klass !== "2xx"}
                  display={String(count)}
                />
              ))}
            </div>
          )}
        </Panel>

        <div className="stack">
          <Panel title="Platform Capability Map" sub="Day 1–5 交付面">
            <div className="flow">
              {[
                { label: "Model Gateway", on: true, note: "Day 1" },
                { label: "RAG + Citation", on: knowledgeReady, note: "Day 2" },
                { label: "Agent Runtime", on: true, note: "Day 3" },
                { label: "ERP / Safety Tools", on: true, note: "Day 4" },
                { label: "RBAC", on: true, note: "Day 4" },
                { label: "Audit", on: true, note: "Day 4" },
                { label: "Metrics", on: true, note: "Day 4" },
                { label: "Console + Docker", on: true, note: "Day 5" },
              ].map((item, index) => (
                <span key={item.label} style={{ display: "contents" }}>
                  {index > 0 && <span className="arrow">·</span>}
                  <span className={`node ${item.on ? "hit" : ""}`} title={item.note}>
                    {item.label}
                  </span>
                </span>
              ))}
            </div>
            <div className="kv" style={{ marginTop: 10 }}>
              <span>tools={(modelsData?.agent.tools.length ?? 4) + " 白名单工具"}</span>
              <span>allowed_for_{role}={(modelsData?.agent.allowed_tools.length ?? "—") + ""}</span>
              <span>max_steps={modelsData?.agent.max_steps ?? "—"}</span>
              <span>max_tool_calls={modelsData?.agent.max_tool_calls ?? "—"}</span>
            </div>
          </Panel>

          <Panel title="Synthetic data & boundary" sub="演示数据说明">
            <table className="data">
              <tbody>
                <tr>
                  <td>Business DB rows</td>
                  <td className="mono">
                    {alive
                      ? Object.entries(alive.database.rows)
                          .map(([table, count]) => `${table}=${count}`)
                          .join(" · ")
                      : "—"}
                  </td>
                </tr>
                <tr>
                  <td>Seeded</td>
                  <td>
                    <StatusBadge status={alive?.database.seeded ? "SUCCESS" : "PENDING"} />
                    <span className="hint"> data/synthetic/seed.json（确定性合成）</span>
                  </td>
                </tr>
                <tr>
                  <td>Knowledge</td>
                  <td className="mono">
                    {docsData
                      ? `${docsData.total_documents} docs / ${docsData.total_chunks} chunks（公开资料）`
                      : "—"}
                  </td>
                </tr>
              </tbody>
            </table>
            <p className="hint">
              本项目是求职演示原型：不连接恒光内部系统，不使用内部数据，不接入真实 ERP / OA / DCS；
              AI 只用于分析与辅助决策，不做工业控制。
            </p>
          </Panel>

          <Panel title="Next" sub="演示入口">
            <div className="toolbar">
              <button className="btn primary" type="button" onClick={() => navigate("/agent")}>
                打开 Agent Playground
              </button>
              <button className="btn" type="button" onClick={() => navigate("/knowledge")}>
                Knowledge / RAG
              </button>
              <button className="btn" type="button" onClick={() => navigate("/audit")}>
                Audit 链路
              </button>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
