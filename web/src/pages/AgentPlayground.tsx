/**
 * Agent Playground — the demo centrepiece (Day 5 P0 #2, #3, #9).
 *
 * Left: the conversation (what the user asked, what the platform answered, with
 * model / provider / latency / request_id / sources). Right: the *why* — the
 * execution trace, the tool calls with their permission outcome, and the citations.
 *
 * The page has no permission logic of its own: it sends the selected demo role's
 * bearer token and renders whatever the backend decides. An operator asking an
 * ERP question therefore produces HTTP 200 + `tool_calls[].error_code =
 * PERMISSION_DENIED`, which is exactly the platform behaviour being demonstrated.
 */

import { useCallback, useMemo, useRef, useState } from "react";

import { Badge, EmptyState, Panel, StatusBadge } from "../components/Primitives";
import { FailureState } from "../components/States";
import { FlowStrip, SourcePanel, ToolCallTable, TraceTimeline } from "../components/Trace";
import { pairToolCalls } from "../components/Trace";
import { handoffRequest } from "../app/handoff";
import { navigate } from "../app/router";
import { useDemoUser } from "../app/DemoUserContext";
import { api, asFailure } from "../services/api";
import type { AgentRunResponse, ApiFailure } from "../types";

const DEMO_PROMPTS: { label: string; message: string; expect: string }[] = [
  {
    label: "① 业务概览 (RAG)",
    message: "恒光主要有哪些业务？",
    expect: "knowledge_search → RAG → 引用来源",
  },
  {
    label: "② 采购价格 (ERP)",
    message: "最近30天主要原材料采购价格有什么变化？",
    expect: "erp_purchase_analysis（operator 会被拒绝）",
  },
  {
    label: "③ 区域安全 (Safety)",
    message: "最近一个月哪个区域安全问题最多？",
    expect: "safety_incident_analysis → incident_by_area",
  },
  {
    label: "④ 车间特征 (Safety)",
    message: "A车间最近安全问题有什么特点？",
    expect: "safety tool + 类别/等级统计",
  },
  {
    label: "⑤ 年报详情 (Doc)",
    message: "查看恒光2025年年报的详细信息",
    expect: "document_lookup → 文档 metadata",
  },
];

interface Turn {
  id: string;
  question: string;
  answer: string | null;
  result: AgentRunResponse | null;
  failure: ApiFailure | null;
  role: string;
  username: string;
  at: string;
}

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function AgentPlayground() {
  const { identity, role } = useDemoUser();
  const [input, setInput] = useState(DEMO_PROMPTS[0].message);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const threadRef = useRef<HTMLDivElement | null>(null);

  const selected = useMemo(
    () => turns.find((turn) => turn.id === selectedId) ?? turns[turns.length - 1] ?? null,
    [turns, selectedId],
  );

  const run = useCallback(
    async (message: string) => {
      const question = message.trim();
      if (!question || running) return;
      const id = newId();
      const turn: Turn = {
        id,
        question,
        answer: null,
        result: null,
        failure: null,
        role,
        username: identity.username,
        at: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
      };
      setTurns((current) => [...current, turn]);
      setSelectedId(id);
      setRunning(true);
      setInput("");
      try {
        const result = await api.agentRun({ message: question });
        setTurns((current) =>
          current.map((item) =>
            item.id === id
              ? { ...item, result, answer: result.answer, failure: null }
              : item,
          ),
        );
      } catch (error) {
        const failure = asFailure(error);
        setTurns((current) =>
          current.map((item) => (item.id === id ? { ...item, failure } : item)),
        );
      } finally {
        setRunning(false);
        window.requestAnimationFrame(() => {
          threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
        });
      }
    },
    [identity.username, role, running],
  );

  const result = selected?.result ?? null;
  const denied = result
    ? result.tool_calls.filter((call) => call.error_code === "PERMISSION_DENIED")
    : [];

  return (
    <div className="stack">
      <Panel
        title="Run"
        sub="POST /api/agent/run · Authorization: Bearer demo-…-token"
        actions={
          <>
            <Badge tone="info">role: {role}</Badge>
            {turns.length > 0 && (
              <button className="btn small" type="button" onClick={() => setTurns([])}>
                清空会话
              </button>
            )}
          </>
        }
      >
        <div className="stack">
          <div className="toolbar">
            {DEMO_PROMPTS.map((prompt) => (
              <button
                key={prompt.label}
                className="btn chip"
                type="button"
                title={prompt.expect}
                disabled={running}
                onClick={() => {
                  setInput(prompt.message);
                  void run(prompt.message);
                }}
              >
                {prompt.label}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
            <textarea
              rows={2}
              style={{ flex: 1, resize: "vertical", lineHeight: 1.5 }}
              value={input}
              placeholder="向 Agent 提问，例如：最近30天主要原材料采购价格有什么变化？"
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                  event.preventDefault();
                  void run(input);
                }
              }}
            />
            <button
              className="btn primary"
              type="button"
              disabled={running || !input.trim()}
              onClick={() => void run(input)}
            >
              {running ? (
                <>
                  <span className="spinner" /> Running
                </>
              ) : (
                "Run"
              )}
            </button>
          </div>
          <span className="hint">
            Agent → Model Gateway → 权限检查 → 白名单工具 → 合成数据 / RAG → 回答。
            快捷问题只是输入提示，不改变任何后端逻辑。Ctrl/⌘ + Enter 运行。
          </span>
        </div>
      </Panel>

      <div className="split">
        <Panel title="Conversation" sub={`${turns.length} 轮 · ${identity.username}`}>
          {turns.length === 0 ? (
            <EmptyState
              title="还没有运行记录"
              hint="选一个快捷问题或输入自己的问题，点击 Run。右侧会同步显示 Agent trace、工具调用与引用。"
            />
          ) : (
            <div className="thread" ref={threadRef}>
              {turns.map((turn) => (
                <div key={turn.id} className="stack" style={{ gap: 8 }}>
                  <div className="bubble user">
                    <div className="who">
                      USER <span className="badge">{turn.username} · {turn.role}</span>
                      <span className="badge">{turn.at}</span>
                    </div>
                    <div className="body">{turn.question}</div>
                  </div>
                  {turn.failure ? (
                    <FailureState failure={turn.failure} compact onRetry={() => void run(turn.question)} />
                  ) : turn.result ? (
                    <div
                      className={`bubble ${turn.id === (selected?.id ?? "") ? "" : ""}`}
                      onClick={() => setSelectedId(turn.id)}
                      style={{ cursor: "pointer" }}
                    >
                      <div className="who">
                        AGENT
                        <StatusBadge status={turn.result.status} />
                        {turn.result.tool_calls.some((call) => call.error_code === "PERMISSION_DENIED") && (
                          <Badge tone="err">PERMISSION_DENIED</Badge>
                        )}
                        <span className="badge">{turn.result.provider} / {turn.result.model}</span>
                        <span className="badge">{turn.result.latency_ms} ms</span>
                        <span className="badge">steps {turn.result.steps}</span>
                        <span className="badge">tools {turn.result.tool_calls.length}</span>
                      </div>
                      <div className="body">{turn.result.answer}</div>
                      <div className="meta-grid">
                        <div className="meta">
                          <b>request_id</b>
                          <span className="mono">{turn.result.request_id}</span>
                        </div>
                        <div className="meta">
                          <b>sources</b>
                          <span className="mono">{turn.result.sources.length}</span>
                        </div>
                        <div className="meta">
                          <b>model · provider</b>
                          <span className="mono">
                            {turn.result.model} · {turn.result.provider}
                          </span>
                        </div>
                        <div className="meta">
                          <b>latency</b>
                          <span className="mono">{turn.result.latency_ms} ms</span>
                        </div>
                      </div>
                      <div className="toolbar" style={{ marginTop: 8 }}>
                        <button
                          className="btn small"
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            handoffRequest(turn.result?.request_id ?? "");
                            navigate("/audit");
                          }}
                        >
                          在 Audit 中追踪此 request_id
                        </button>
                        {turn.result.sources.length > 0 && (
                          <span className="hint">
                            引用 {turn.result.sources.map((source) => `[${source.index}]`).join(" ")}
                          </span>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="bubble">
                      <div className="who">
                        AGENT <span className="spinner" /> 运行中…
                      </div>
                      <div className="body hint">
                        Model Gateway 推理 / 工具执行中，trace 会在返回后渲染。
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>

        <div className="stack">
          <Panel title="Execution Path" sub="User → Agent → Tool → LLM → Answer">
            {result ? (
              <FlowStrip trace={result.trace} toolCalls={result.tool_calls} />
            ) : (
              <p className="hint">运行一次提问后，这里会点亮真实经过的节点。</p>
            )}
            {denied.length > 0 && (
              <div className="state denied" style={{ marginTop: 10 }}>
                <h3>
                  <Badge tone="err">PERMISSION_DENIED</Badge> {denied[0].name}
                </h3>
                <p>
                  角色 <b className="mono">{role}</b> 没有该工具的权限，调用被 ToolExecutor 在执行前拒绝；
                  HTTP 仍为 200，Agent 用一段说明收尾，没有堆栈信息。审计里留下的是
                  <span className="mono"> tool.call=denied</span>。
                </p>
              </div>
            )}
          </Panel>

          <Panel title="Agent Trace" sub={result ? `${result.trace.length} 条事件` : "等待运行"}>
            {result ? (
              <TraceTimeline trace={result.trace} toolCalls={result.tool_calls} />
            ) : (
              <p className="hint">选择左侧一轮回答查看 step-by-step trace。</p>
            )}
          </Panel>

          <Panel title="Tool Calls" sub={result ? `${result.tool_calls.length} 次执行` : "等待运行"}>
            {result ? (
              <ToolCallTable calls={pairToolCalls(result.tool_calls, result.trace)} />
            ) : (
              <p className="hint">工具名 / operation / 状态 / 延迟 / 结果数量会显示在这里。</p>
            )}
          </Panel>

          <Panel title="Sources / Citations" sub={result ? `${result.sources.length} 条` : "等待运行"}>
            {result ? (
              <SourcePanel sources={result.sources} />
            ) : (
              <p className="hint">RAG 命中时这里列出 document_id / section / page / score / citation。</p>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
