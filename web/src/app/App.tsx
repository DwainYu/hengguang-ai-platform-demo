/**
 * Console shell: sidebar navigation, live header strip, demo-role switcher.
 *
 * The header reads `GET /health` + `GET /metrics` — both public endpoints — so the
 * shell proves the API wiring before any page renders, and never needs a role that
 * can see the model catalogue. The role switcher only decides which bearer token
 * `services/api.ts` sends; every real decision stays on the server.
 */

import { useCallback } from "react";

import { Badge } from "../components/Primitives";
import { DemoUserProvider, ROLE_CAPABILITIES, useDemoUser } from "./DemoUserContext";
import { ROUTES, useRoute, type RoutePath } from "./router";
import { useAsync } from "../hooks/useAsync";
import { AgentPlayground } from "../pages/AgentPlayground";
import { Audit } from "../pages/Audit";
import { Dashboard } from "../pages/Dashboard";
import { Knowledge } from "../pages/Knowledge";
import { Settings } from "../pages/Settings";
import { api } from "../services/api";
import type { DemoRole } from "../types";

const ROLE_LABEL: Record<DemoRole, string> = {
  admin: "Admin",
  manager: "Manager",
  operator: "Operator",
};

const PAGE_META: Record<RoutePath, { title: string; blurb: string }> = {
  "/": {
    title: "Dashboard",
    blurb: "Model Gateway · RAG · Agent · 业务工具 · RBAC · 审计 · 指标 —— 平台实时状态",
  },
  "/agent": {
    title: "Agent Playground",
    blurb: "一次提问 → Model Gateway → 权限校验 → 白名单工具 → 带引用的回答 + 完整 trace",
  },
  "/knowledge": {
    title: "Knowledge",
    blurb: "公开资料知识库：文档 / chunk 统计、带 citation 的检索、admin 重建",
  },
  "/audit": {
    title: "Audit",
    blurb: "一个 request_id 追完 HTTP → Agent → Tool → Audit 的整条链路",
  },
  "/settings": {
    title: "Settings",
    blurb: "演示身份、模型目录、工具白名单与角色权限矩阵",
  },
};

function RoleSwitcher() {
  const { role, setRole, identity } = useDemoUser();
  return (
    <div className="toolbar">
      <span className="hint">Demo role</span>
      <div className="seg" role="group" aria-label="切换演示角色">
        {(Object.keys(ROLE_CAPABILITIES) as DemoRole[]).map((candidate) => (
          <button
            key={candidate}
            type="button"
            className={candidate === role ? "active" : ""}
            onClick={() => setRole(candidate)}
            title={`Authorization: Bearer ${identity.token}`}
          >
            {ROLE_LABEL[candidate]}
          </button>
        ))}
      </div>
      <Badge tone="info" title={`当前身份：${identity.username}`}>
        {identity.username} · {identity.role}
      </Badge>
    </div>
  );
}

function HeaderStatus() {
  const { revision } = useDemoUser();
  const load = useCallback(
    (signal: AbortSignal) =>
      Promise.all([api.health(signal), api.metrics(signal)]).then(([health, metrics]) => ({
        provider: metrics.app.provider,
        version: health.version,
        requests: metrics.request_count,
      })),
    [],
  );
  const { data, error } = useAsync(load, [revision]);

  return (
    <div className="toolbar" title={error ? error.message : "GET /health · GET /metrics"}>
      <Badge tone={data ? "ok" : "err"} dot>
        {data ? "API healthy" : "API unreachable"}
      </Badge>
      <span className="tag">
        provider <b>{data?.provider ?? "—"}</b> · v{data?.version ?? "—"} · requests{" "}
        <b>{data?.requests ?? 0}</b>
      </span>
    </div>
  );
}

function Shell() {
  const path = useRoute();
  const meta = PAGE_META[path];
  return (
    <div className="console">
      <aside className="sidebar">
        <div className="brand">
          <strong>Hengguang AI Platform</strong>
          <span>enterprise AI console · demo</span>
        </div>
        <nav className="nav">
          {ROUTES.map((route) => (
            <a
              key={route.path}
              href={`#${route.path}`}
              className={route.path === path ? "active" : ""}
            >
              <b>{route.label}</b>
              <i>{route.hint}</i>
            </a>
          ))}
        </nav>
        <div className="side-foot">
          <span className="tag">数据边界 / data boundary</span>
          <span className="hint">
            知识库＝公开资料；ERP / 安全＝<code>data/synthetic</code> 合成数据。AI 只做分析与辅助决策，
            不接入真实 DCS / ERP，不做工业控制。
          </span>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <h1>{meta.title}</h1>
            <p>{meta.blurb}</p>
          </div>
          <div className="toolbar">
            <HeaderStatus />
            <RoleSwitcher />
          </div>
        </div>
        {path === "/" && <Dashboard />}
        {path === "/agent" && <AgentPlayground />}
        {path === "/knowledge" && <Knowledge />}
        {path === "/audit" && <Audit />}
        {path === "/settings" && <Settings />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <DemoUserProvider>
      <Shell />
    </DemoUserProvider>
  );
}
