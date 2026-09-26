/** Small presentational building blocks shared by every console page. */

import type { ReactNode } from "react";

export function Panel({
  title,
  sub,
  actions,
  children,
  className = "",
}: {
  title?: string;
  sub?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <header className="panel-head">
          <div>
            {title && <h2>{title}</h2>}
            {sub && <div className="sub">{sub}</div>}
          </div>
          {actions && <div className="toolbar">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export type Tone = "neutral" | "ok" | "warn" | "err" | "info";

const TONE_CLASS: Record<Tone, string> = {
  neutral: "",
  ok: "ok",
  warn: "warn",
  err: "err",
  info: "info",
};

export function Badge({
  children,
  tone = "neutral",
  dot = false,
  title,
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  title?: string;
}) {
  return (
    <span className={`badge ${TONE_CLASS[tone]}`} title={title}>
      {dot && <i className="dot" />}
      {children}
    </span>
  );
}

/** Map an audit / tool-call status to badge tone + label. */
export function StatusBadge({ status }: { status: string | null | undefined }) {
  const value = (status ?? "unknown").toUpperCase();
  const tone: Tone =
    value === "SUCCESS" || value === "OK" || value === "COMPLETED"
      ? "ok"
      : value === "DENIED" || value === "PERMISSION_DENIED"
        ? "err"
        : value === "ERROR" || value === "FAILED" || value === "TOOL_ERROR"
          ? "err"
          : value === "PENDING" || value === "RUNNING"
            ? "info"
            : "neutral";
  return (
    <Badge tone={tone} dot>
      {value}
    </Badge>
  );
}

export function StatCard({
  label,
  value,
  foot,
  badge,
  small = false,
}: {
  label: string;
  value: ReactNode;
  foot?: ReactNode;
  badge?: ReactNode;
  small?: boolean;
}) {
  return (
    <div className="panel">
      <div className="card-label">
        {label}
        {badge}
      </div>
      <div className={`card-value ${small ? "small" : ""}`}>{value}</div>
      {foot && <div className="card-foot">{foot}</div>}
    </div>
  );
}

/** Horizontal CSS bar (used for the metrics breakdown — no chart library). */
export function BarRow({
  label,
  value,
  max,
  display,
  warn = false,
}: {
  label: string;
  value: number;
  max: number;
  display?: string;
  warn?: boolean;
}) {
  const pct = max > 0 ? Math.max(2, Math.round((value / max) * 100)) : 0;
  return (
    <div className="bar-row">
      <span className="tag" title={label}>
        {label}
      </span>
      <span className="bar-track">
        <span className={`bar-fill ${warn ? "warn" : ""}`} style={{ width: `${pct}%` }} />
      </span>
      <span className="bar-value">{display ?? String(value)}</span>
    </div>
  );
}

export function KeyValue({ items }: { items: { key: string; value: ReactNode }[] }) {
  return (
    <div className="meta-grid">
      {items.map((item) => (
        <div className="meta" key={item.key}>
          <b>{item.key}</b>
          <span className="mono" style={{ color: "var(--text)" }}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export function Loading({ text = "加载中…" }: { text?: string }) {
  return (
    <div className="state">
      <h3>
        <span className="spinner" /> {text}
      </h3>
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="state">
      <h3>{title}</h3>
      {hint && <p>{hint}</p>}
      {action}
    </div>
  );
}
