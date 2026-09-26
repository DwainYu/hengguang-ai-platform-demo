/**
 * Settings / Models — identity, model catalogue, permission matrix, and a direct
 * Model Gateway probe.
 *
 * Everything is read from the platform: `GET /api/models` (chat + embedding
 * models, tool whitelist, agent limits, *the caller's own permissions*) and
 * `GET /api/users` (admin only: the three demo accounts + which roles hold the
 * sensitive permissions). `/api/chat` here is the Day-1 direct path, which is also
 * the only endpoint that accepts a `model` override — that is where the simple
 * model switch lives, because the agent loop intentionally has no model parameter.
 */

import { useCallback, useState } from "react";

import { Badge, Loading, Panel, StatusBadge } from "../components/Primitives";
import { FailureState } from "../components/States";
import { ROLE_CAPABILITIES, useDemoUser } from "../app/DemoUserContext";
import { useAsync } from "../hooks/useAsync";
import { api, asFailure } from "../services/api";
import type { ChatResponse, DemoRole, ModelInfo } from "../types";

const MATRIX: { permission: string; note: string }[] = [
  { permission: "chat:run", note: "POST /api/chat（直连 Model Gateway）" },
  { permission: "agent:run", note: "POST /api/agent/run" },
  { permission: "knowledge:query", note: "检索 + 文档清单" },
  { permission: "knowledge:ingest", note: "重建知识库" },
  { permission: "models:list", note: "GET /api/models" },
  { permission: "audit:read", note: "GET /api/audit" },
  { permission: "users:manage", note: "GET /api/users" },
  { permission: "tool:knowledge", note: "knowledge_search / document_lookup" },
  { permission: "tool:erp", note: "erp_purchase_analysis" },
  { permission: "tool:safety", note: "safety_incident_analysis" },
];

/** Which demo roles hold each permission (mirrors app/auth/permissions.py). */
const HOLDERS: Record<string, DemoRole[]> = {
  "chat:run": ["admin", "manager", "operator"],
  "agent:run": ["admin", "manager", "operator"],
  "knowledge:query": ["admin", "manager", "operator"],
  "knowledge:ingest": ["admin"],
  "models:list": ["admin", "manager"],
  "audit:read": ["admin", "manager"],
  "users:manage": ["admin"],
  "tool:knowledge": ["admin", "manager", "operator"],
  "tool:erp": ["admin", "manager"],
  "tool:safety": ["admin", "manager", "operator"],
};

function GatewayProbe({ models }: { models: ModelInfo[] }) {
  const [message, setMessage] = useState("恒光主要有哪些业务？");
  const [model, setModel] = useState<string>("");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const send = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      setAnswer(await api.chat({ message, model: model || null }));
    } catch (failure) {
      setAnswer(null);
      setError(asFailure(failure).message);
    } finally {
      setBusy(false);
    }
  }, [message, model]);

  return (
    <div className="stack">
      <div className="toolbar">
        <input
          style={{ flex: 1, minWidth: 240 }}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="直连模型的问题（不经过 Agent / 工具）"
        />
        <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          model
          <select value={model} onChange={(event) => setModel(event.target.value)}>
            <option value="">provider default</option>
            {models.map((entry) => (
              <option key={`${entry.kind}-${entry.model}`} value={entry.model}>
                {entry.kind} · {entry.provider} / {entry.model}
              </option>
            ))}
          </select>
        </label>
        <button className="btn primary" type="button" disabled={busy} onClick={() => void send()}>
          {busy ? <span className="spinner" /> : null} POST /api/chat
        </button>
      </div>
      {error && <p className="hint" style={{ color: "var(--err)" }}>{error}</p>}
      {answer && (
        <>
          <div className="row">
            <Badge tone="ok">{answer.provider}</Badge>
            <Badge>{answer.model}</Badge>
            <Badge>{answer.latency_ms} ms</Badge>
            <span className="tag">request_id {answer.request_id}</span>
            <span className="tag">
              {answer.user} · {answer.role}
            </span>
          </div>
          <div className="answer-box">{answer.answer}</div>
        </>
      )}
    </div>
  );
}

export function Settings() {
  const { revision, role, setRole, identity } = useDemoUser();

  const loadModels = useCallback((signal: AbortSignal) => api.models(signal), []);
  const loadUsers = useCallback((signal: AbortSignal) => api.users(signal), []);
  const models = useAsync(loadModels, [revision]);
  const users = useAsync(loadUsers, [revision]);

  const chatModels = (models.data?.models ?? []).filter((item) => item.kind === "chat");
  const embeddingModels = (models.data?.models ?? []).filter((item) => item.kind === "embedding");

  return (
    <div className="stack">
      <div className="split">
        <Panel title="Demo identity" sub="固定 bearer token（app/auth/auth.py）">
          <div className="stack">
            <div className="seg">
              {(["admin", "manager", "operator"] as DemoRole[]).map((candidate) => (
                <button
                  key={candidate}
                  type="button"
                  className={candidate === role ? "active" : ""}
                  onClick={() => setRole(candidate)}
                >
                  {candidate}
                </button>
              ))}
            </div>
            <table className="data">
              <tbody>
                <tr>
                  <td>username</td>
                  <td className="mono">{identity.username}</td>
                </tr>
                <tr>
                  <td>role</td>
                  <td className="mono">{identity.role}</td>
                </tr>
                <tr>
                  <td>Authorization</td>
                  <td className="mono">Bearer {identity.token}</td>
                </tr>
              </tbody>
            </table>
            <div className="card-label">该角色能力（仅用于选按钮，不是安全边界）</div>
            <ul className="hint" style={{ margin: 0, paddingLeft: 18 }}>
              {ROLE_CAPABILITIES[role].map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="hint">
              权限由后端判定：<code>app/auth/dependencies.py</code>（路由）+{" "}
              <code>app/agent/executor.py</code>（工具）。手工用 operator token 调 ERP 工具，
              一样得到 <code>PERMISSION_DENIED</code>。
            </p>
          </div>
        </Panel>

        <Panel title="Permission matrix" sub="GET /api/models · permissions[]">
          {models.error ? (
            <FailureState
              failure={models.error}
              compact
              onRetry={models.reload}
              hint={`角色 ${role} 没有 models:list；下表为 app/auth/permissions.py 的矩阵（后端仍是唯一事实来源）。`}
            />
          ) : models.loading && !models.data ? (
            <Loading text="读取模型目录…" />
          ) : (
            <div className="scroll-x">
              <table className="data">
                <thead>
                  <tr>
                    <th>permission</th>
                    <th>admin</th>
                    <th>manager</th>
                    <th>operator</th>
                    <th>说明</th>
                  </tr>
                </thead>
                <tbody>
                  {MATRIX.map((row) => (
                    <tr key={row.permission}>
                      <td className="mono">
                        {row.permission}
                        {models.data?.permissions.includes(row.permission) && (
                          <span className="badge ok" style={{ marginLeft: 6 }}>
                            你有
                          </span>
                        )}
                      </td>
                      {(["admin", "manager", "operator"] as DemoRole[]).map((candidate) => (
                        <td key={candidate}>
                          {HOLDERS[row.permission]?.includes(candidate) ? (
                            <Badge tone="ok">✓</Badge>
                          ) : (
                            <Badge tone="err">—</Badge>
                          )}
                        </td>
                      ))}
                      <td className="hint">{row.note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>

      <Panel
        title="Model Gateway"
        sub="GET /api/models · 不返回任何密钥 / base URL / token"
        actions={
          <button className="btn small" type="button" onClick={models.reload}>
            刷新
          </button>
        }
      >
        {models.error ? (
          <FailureState failure={models.error} compact onRetry={models.reload} />
        ) : models.loading && !models.data ? (
          <Loading text="读取模型目录…" />
        ) : (
          <div className="stack">
            <div className="scroll-x">
              <table className="data">
                <thead>
                  <tr>
                    <th>kind</th>
                    <th>provider</th>
                    <th>model</th>
                    <th>available</th>
                    <th>default</th>
                  </tr>
                </thead>
                <tbody>
                  {[...chatModels, ...embeddingModels].map((entry) => (
                    <tr key={`${entry.kind}-${entry.provider}-${entry.model}`}>
                      <td>
                        <Badge tone={entry.kind === "chat" ? "info" : "neutral"}>{entry.kind}</Badge>
                      </td>
                      <td className="mono">{entry.provider}</td>
                      <td className="mono">{entry.model}</td>
                      <td>
                        <StatusBadge status={entry.available ? "SUCCESS" : "ERROR"} />
                      </td>
                      <td className="tag">{entry.default ? "default" : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="divider" />
            <div className="card-label">Model Gateway 直连测试（POST /api/chat，可覆盖 model）</div>
            <GatewayProbe models={[...chatModels, ...embeddingModels]} />
            <p className="hint">
              默认 <code>LLM_PROVIDER=mock</code>：零 API Key、零外网即可跑完整链路。
              配好 <code>LLM_BASE_URL</code> / <code>LLM_API_KEY</code> / <code>LLM_MODEL</code>{" "}
              后这里直接走真实模型；密钥永远只留在环境变量里。
            </p>
          </div>
        )}
      </Panel>

      <div className="split">
        <Panel title="Agent runtime" sub="白名单工具与安全限制">
          {models.error ? (
            <FailureState failure={models.error} compact onRetry={models.reload} />
          ) : (
            <div className="stack">
              <table className="data">
                <thead>
                  <tr>
                    <th>tool</th>
                    <th>required permission</th>
                    <th>role {role}</th>
                  </tr>
                </thead>
                <tbody>
                  {(models.data?.agent.tools ?? []).map((tool) => (
                    <tr key={tool}>
                      <td className="mono">{tool}</td>
                      <td className="mono tag">
                        {tool === "erp_purchase_analysis"
                          ? "tool:erp"
                          : tool === "safety_incident_analysis"
                            ? "tool:safety"
                            : "tool:knowledge"}
                      </td>
                      <td>
                        {models.data?.agent.allowed_tools.includes(tool) ? (
                          <Badge tone="ok">allowed</Badge>
                        ) : (
                          <Badge tone="err">PERMISSION_DENIED</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="kv">
                <span>max_steps={models.data?.agent.max_steps ?? "—"}</span>
                <span>max_tool_calls={models.data?.agent.max_tool_calls ?? "—"}</span>
                <span>AGENT_MAX_STEPS / AGENT_MAX_TOOL_CALLS</span>
              </div>
            </div>
          )}
        </Panel>

        <Panel title="Demo accounts" sub="GET /api/users · users:manage = admin">
          {users.error ? (
            <FailureState
              failure={users.error}
              compact
              onRetry={users.reload}
              hint={`该目录仅 admin 可见；当前角色 ${role} 收到 403 是预期行为。`}
            />
          ) : users.loading && !users.data ? (
            <Loading text="读取演示账号…" />
          ) : (
            <div className="scroll-x">
              <table className="data">
                <thead>
                  <tr>
                    <th>username</th>
                    <th>role</th>
                    <th>permissions</th>
                  </tr>
                </thead>
                <tbody>
                  {(users.data?.users ?? []).map((entry) => (
                    <tr key={entry.id}>
                      <td className="mono">{entry.username}</td>
                      <td>
                        <Badge tone="info">{entry.role}</Badge>
                      </td>
                      <td className="hint">{entry.permissions.join(" · ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="card-label" style={{ marginTop: 10 }}>
                敏感权限的持有角色
              </div>
              <div className="kv">
                {Object.entries(users.data?.permission_roles ?? {}).map(([permission, roles]) => (
                  <span key={permission}>
                    {permission}={roles.join("/")}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
