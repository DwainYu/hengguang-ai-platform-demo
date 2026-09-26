/**
 * Error / permission states derived from the platform error envelope.
 *
 * A 401/403 must read as "Permission denied" (with the missing permission when
 * the backend tells us), never as a stack trace; a 5xx must surface the
 * `request_id` so the same number can be pasted into `GET /api/audit/{id}`.
 */

import type { ReactNode } from "react";

import type { ApiFailure } from "../types";
import { Badge, Panel } from "./Primitives";

export function FailureState({
  failure,
  hint,
  onRetry,
  compact = false,
}: {
  failure: ApiFailure;
  hint?: ReactNode;
  onRetry?: () => void;
  compact?: boolean;
}) {
  const body = (
    <>
      <h3>
        {failure.denied ? "Permission denied." : "Request failed"}
        <Badge tone={failure.denied ? "warn" : "err"}>{failure.code}</Badge>
      </h3>
      <p>{failure.message}</p>
      {hint && <p>{hint}</p>}
      <div className="rid mono">
        HTTP {failure.status || "—"}
        {failure.request_id && ` · request_id: ${failure.request_id}`}
        {failure.details && Object.keys(failure.details).length > 0
          ? ` · ${formatDetails(failure.details)}`
          : ""}
      </div>
      {onRetry && (
        <button className="btn small" onClick={onRetry} type="button">
          重试
        </button>
      )}
    </>
  );

  if (compact) {
    return <div className={`state ${failure.denied ? "denied" : "error"}`}>{body}</div>;
  }
  return (
    <Panel title={failure.denied ? "权限不足" : "请求失败"}>
      <div className={`state ${failure.denied ? "denied" : "error"}`}>{body}</div>
    </Panel>
  );
}

/** `details` carries machine-readable extras (`required_permission`, `role`, …). */
export function formatDetails(details: Record<string, unknown>): string {
  return Object.entries(details)
    .filter(([, value]) => typeof value !== "object" || value === null)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join(" · ");
}

/**
 * Backend `CONFLICT` on the knowledge endpoints means "nothing ingested yet";
 * render it as the product-level empty state instead of an error.
 */
export function isKnowledgeNotReady(failure: ApiFailure | null): boolean {
  return failure?.code === "CONFLICT" || failure?.status === 409;
}
