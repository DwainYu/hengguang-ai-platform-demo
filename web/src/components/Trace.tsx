/**
 * Agent trace visualisation (Day 5 P0 #3).
 *
 * The runtime already emits everything needed — `trace` (llm / tool_call / final
 * / stopped), `tool_calls` (name, operation, success, error_code, result_count)
 * and `sources`. This module only *renders* that payload; it never recomputes
 * permissions and never shows a stack trace: a denied tool is exactly one
 * `PERMISSION_DENIED` badge plus the controlled message the backend returned.
 *
 * Pairing rule: the k-th `tool_call` trace entry belongs to the k-th `tool_calls`
 * item — the runtime appends both in the same loop, so that index is the
 * correlation key that gives every tool row its own latency and result detail.
 */

import type { AgentSource, AgentToolCall, AgentTraceStep } from "../types";
import { Badge, Panel, StatusBadge } from "./Primitives";

export type ToolCallView = AgentToolCall & {
  latency_ms: number;
  /** Trace detail of this exact call, e.g. `5 chunks` / `10 rows`. */
  detail: string | null;
};

/** `tool_calls` joined with their `tool_call` trace entries, in execution order. */
export function pairToolCalls(toolCalls: AgentToolCall[], trace: AgentTraceStep[]): ToolCallView[] {
  const entries = trace.filter((entry) => entry.type === "tool_call");
  return toolCalls.map((call, index) => {
    const entry = entries[index];
    const matched = entry && entry.tool === call.name ? entry : undefined;
    return { ...call, latency_ms: matched?.latency_ms ?? 0, detail: matched?.detail ?? null };
  });
}

function outcomeOf(call: AgentToolCall): "ok" | "denied" | "error" {
  if (call.error_code === "PERMISSION_DENIED") return "denied";
  return call.success ? "ok" : "error";
}

/** `User → Auth → Agent → Model Gateway → <tools> → Answer`, nodes lit by what ran. */
export function FlowStrip({
  trace,
  toolCalls,
}: {
  trace: AgentTraceStep[];
  toolCalls: AgentToolCall[];
}) {
  const names = new Set(toolCalls.map((call) => call.name));
  const business = (name: string) => name !== "knowledge_search" && name !== "document_lookup";
  const hasRag = names.has("knowledge_search") || names.has("document_lookup");
  const hasBusiness = [...names].some(business);
  const finished = trace.some((entry) => entry.type === "final");
  const nodes: { label: string; on: boolean }[] = [
    { label: "User", on: true },
    { label: "Auth · RBAC", on: true },
    { label: "Agent Runtime", on: trace.length > 0 },
    { label: "Model Gateway → LLM", on: trace.some((entry) => entry.type === "llm") },
    { label: "knowledge_search · RAG", on: hasRag },
    { label: "ERP / Safety Tool", on: hasBusiness },
    { label: finished ? "Answer" : "安全停止", on: true },
  ];
  return (
    <div className="flow">
      {nodes.map((node, index) => (
        <span key={node.label} style={{ display: "contents" }}>
          {index > 0 && <span className="arrow">→</span>}
          <span className={`node ${node.on ? "hit" : ""}`} title={node.on ? "本轮经过" : "本轮未触发"}>
            {node.label}
          </span>
        </span>
      ))}
    </div>
  );
}

type EntryView = { title: string; sub?: string; note?: string };

/**
 * A `tool_call` trace entry only says *which* tool ran, so the row inherits its
 * outcome from the paired `tool_calls` item (permission / argument / data errors
 * are different stories in the UI).
 */
function describeEntry(entry: AgentTraceStep, call?: ToolCallView): EntryView {
  switch (entry.type) {
    case "llm":
      return entry.tool
        ? { title: "LLM → 请求调用工具", sub: entry.tool }
        : { title: "LLM → 生成最终回答", sub: `第 ${entry.step} 轮模型推理` };
    case "tool_call": {
      const name = call?.name ?? entry.tool ?? "unknown";
      if (call?.error_code === "PERMISSION_DENIED") {
        return {
          title: `${name} → 被权限边界拒绝`,
          sub: `需要权限 ${String(call.error ?? "").match(/需要权限 '([^']+)'/)?.[1] ?? "tool:*"}`,
          note: "PERMISSION_DENIED：工具未执行，没有触达任何数据",
        };
      }
      if (call && call.success === false) {
        return { title: `${name} → 执行失败`, sub: call.error_code ?? "TOOL_ERROR", note: entry.detail ?? undefined };
      }
      return { title: `${name} → 工具结果`, sub: entry.detail ?? undefined };
    }
    case "final":
      return { title: "Final answer", sub: "回答 + 引用返回调用方" };
    case "stopped":
      return { title: "安全限制停止", sub: entry.detail ?? "max_steps / max_tool_calls" };
    default:
      return { title: entry.type, sub: entry.detail ?? undefined };
  }
}

export function TraceTimeline({
  trace,
  toolCalls,
}: {
  trace: AgentTraceStep[];
  toolCalls: AgentToolCall[];
}) {
  if (trace.length === 0) return <p className="hint">该响应没有 trace。</p>;
  const paired = pairToolCalls(toolCalls, trace);
  const outcomeByEntry: (string | undefined)[] = [];
  const entryOfTrace = new Map<number, ToolCallView>();
  let executed = -1;
  trace.forEach((entry, index) => {
    if (entry.type !== "tool_call") {
      outcomeByEntry.push(undefined);
      return;
    }
    executed += 1;
    const call = paired[executed];
    if (call) entryOfTrace.set(index, call);
    outcomeByEntry.push(call ? outcomeOf(call) : undefined);
  });

  return (
    <div className="timeline">
      {trace.map((entry, index) => {
        const denied = outcomeByEntry[index] === "denied";
        const failed = outcomeByEntry[index] === "error";
        const info = describeEntry(entry, entryOfTrace.get(index));
        const kind = entry.type === "tool_call" ? (denied ? "denied" : "tool") : entry.type === "final" ? "final" : "";
        return (
          <div className="tl-item" key={`${entry.step}-${entry.type}-${index}`}>
            <div className="tl-rail">
              <span className={`tl-index ${kind}`}>{entry.type === "final" ? "✓" : index + 1}</span>
            </div>
            <div className="tl-body">
              <div className="tl-title">
                <Badge tone={entry.type === "llm" ? "info" : "neutral"}>
                  {entry.type.toUpperCase()}
                </Badge>
                <span>{info.title}</span>
                <Badge tone={denied || failed ? "err" : "neutral"}>{entry.latency_ms} ms</Badge>
              </div>
              {info.sub && <div className="tl-sub">{info.sub}</div>}
              {info.note && (
                <div className="tl-sub" style={{ color: "var(--err)" }}>
                  {info.note}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ToolCallTable({ calls }: { calls: ToolCallView[] }) {
  if (calls.length === 0) return <p className="hint">本轮没有工具调用（模型直接回答）。</p>;
  return (
    <div className="stack">
      {calls.map((call, index) => {
        const outcome = outcomeOf(call);
        return (
          <div className={`call-block ${outcome}`} key={`${call.name}-${index}`}>
            <div className="tl-title">
              <span className="tag mono">#{index + 1}</span>
              <b className="mono">{call.name}</b>
              <StatusBadge
                status={
                  call.error_code === "PERMISSION_DENIED"
                    ? "PERMISSION_DENIED"
                    : call.success
                      ? "SUCCESS"
                      : (call.error_code ?? "ERROR")
                }
              />
              <Badge>{call.latency_ms} ms</Badge>
            </div>
            <div className="kv">
              {call.operation && <span>operation={call.operation}</span>}
              {call.result_count !== null && <span>results={call.result_count}</span>}
              {call.detail && <span>{call.detail}</span>}
              {Object.entries(call.arguments).map(([key, value]) => (
                <span key={key}>
                  {key}=
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </span>
              ))}
            </div>
            {call.error && (
              <div className="tl-sub" style={{ marginTop: 6, color: "var(--err)" }}>
                {call.error}
                <span style={{ display: "block", color: "var(--text-faint)" }}>
                  受控失败：不返回堆栈信息；在 Audit 页用同一个 request_id 可追踪该次调用。
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function SourcePanel({ sources }: { sources: AgentSource[] }) {
  if (sources.length === 0) {
    return <p className="hint">本轮回答没有引用知识库来源（业务工具数据或模型直答）。</p>;
  }
  return (
    <div className="stack">
      {sources.map((source, index) => (
        <div className="source" key={`${source.document_id}-${index}`}>
          <div className="head">
            <Badge tone="info">[{source.index ?? index + 1}]</Badge>
            <span className="cite">{source.citation || source.title}</span>
          </div>
          <div className="kv">
            <span>document_id={source.document_id}</span>
            {source.section && <span>section={source.section}</span>}
            {source.page !== null && <span>page={source.page}</span>}
            {source.score !== null && <span>score={source.score.toFixed(4)}</span>}
            <span>source={source.source}</span>
          </div>
          {source.url && (
            <a className="link" href={source.url} target="_blank" rel="noreferrer">
              {source.url}
            </a>
          )}
        </div>
      ))}
    </div>
  );
}

export function TracePanel({
  trace,
  toolCalls,
  sources,
}: {
  trace: AgentTraceStep[];
  toolCalls: AgentToolCall[];
  sources: AgentSource[];
}) {
  const paired = pairToolCalls(toolCalls, trace);
  const denied = paired.filter((call) => outcomeOf(call) === "denied").length;
  return (
    <div className="stack">
      <Panel
        title="Agent Trace"
        sub="step · type · tool · latency"
        actions={<StatusBadge status={denied ? "DENIED" : "SUCCESS"} />}
      >
        <TraceTimeline trace={trace} toolCalls={toolCalls} />
      </Panel>
      <Panel title="Tool Calls" sub={`${paired.length} 次执行（含权限拒绝）`}>
        <ToolCallTable calls={paired} />
      </Panel>
      <Panel title="Sources / Citations" sub={`${sources.length} 条`}>
        <SourcePanel sources={sources} />
      </Panel>
    </div>
  );
}
