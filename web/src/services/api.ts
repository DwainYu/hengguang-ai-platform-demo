/**
 * Single API client for the whole console (Day 5).
 *
 * One place owns: base URL, `Authorization` header, JSON encoding, and the
 * conversion of the backend error envelope
 * (`{detail, request_id, error:{code,message,details}}`) into a typed
 * {@link ApiFailure}. Pages never call `fetch` directly and never branch on
 * HTTP internals — they branch on `failure.code` / `failure.denied`.
 *
 * Base URL is same-origin by default: the Vite dev proxy and the nginx
 * container config both forward `/api`, `/health` and `/metrics` to the API.
 */

import type {
  AgentRunResponse,
  ApiFailure,
  AuditListResponse,
  ChatResponse,
  DocumentsResponse,
  HealthResponse,
  IngestResponse,
  MetricsResponse,
  ModelsResponse,
  SearchResponse,
  UsersResponse,
} from "../types";

/** Machine-readable error codes produced by the platform (app/api/errors.py). */
export const ERROR_PERMISSION_DENIED = "PERMISSION_DENIED";
export const ERROR_UNAUTHENTICATED = "UNAUTHENTICATED";
export const ERROR_CONFLICT = "CONFLICT";
export const ERROR_PROVIDER = "PROVIDER_ERROR";

const BASE: string = import.meta.env?.VITE_API_BASE ?? "";

/** Demo bearer tokens (fixed public constants from app/auth/auth.py — not secrets). */
export const DEMO_TOKENS = {
  admin: "demo-admin-token",
  manager: "demo-manager-token",
  operator: "demo-operator-token",
} as const;

let authToken: string = DEMO_TOKENS.manager;

/** Install the bearer token of the selected demo role. */
export function setApiToken(token: string): void {
  authToken = token;
}

export function getApiToken(): string {
  return authToken;
}

export class ApiRequestError extends Error implements ApiFailure {
  status: number;
  code: string;
  request_id: string;
  details: Record<string, unknown>;
  denied: boolean;

  constructor(input: Partial<ApiFailure> & { status: number; message: string }) {
    super(input.message);
    this.name = "ApiRequestError";
    this.status = input.status;
    this.code = input.code ?? "HTTP_ERROR";
    this.message = input.message;
    this.request_id = input.request_id ?? "";
    this.details = input.details ?? {};
    this.denied = input.denied ?? (input.status === 401 || input.status === 403);
  }
}

function normalizeFailure(status: number, payload: unknown, fallbackMessage: string): ApiFailure {
  const body = (payload ?? {}) as {
    detail?: unknown;
    request_id?: unknown;
    error?: { code?: unknown; message?: unknown; details?: unknown };
  };
  const envelope = body.error ?? {};
  const message =
    typeof envelope.message === "string" && envelope.message
      ? envelope.message
      : typeof body.detail === "string" && body.detail
        ? body.detail
        : fallbackMessage;
  return new ApiRequestError({
    status,
    message,
    code:
      typeof envelope.code === "string" ? envelope.code : status === 404 ? "NOT_FOUND" : "HTTP_ERROR",
    request_id: typeof body.request_id === "string" ? body.request_id : "",
    details: (envelope.details ?? {}) as Record<string, unknown>,
    denied: status === 401 || status === 403,
  });
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
  /** Override the role token for a single call (used to probe another role). */
  token?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  const token = options.token ?? authToken;
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    throw new ApiRequestError({
      status: 0,
      code: "NETWORK_ERROR",
      message: `无法连接平台 API（${path}）。请确认后端已启动：uv run uvicorn app.main:app --port 8000`,
      denied: false,
    });
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { detail: text.slice(0, 400) };
    }
  }
  if (!response.ok) {
    throw normalizeFailure(
      response.status,
      payload,
      `请求失败：HTTP ${response.status} ${path}`,
    );
  }
  return payload as T;
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}

export interface AuditFilters {
  page?: number;
  page_size?: number;
  tool?: string;
  action?: string;
  status?: string;
  request_id?: string;
}

/** The whole platform API surface used by the console. */
export const api = {
  /** GET /health — public liveness + seeded database probe. */
  health: (signal?: AbortSignal) => request<HealthResponse>("/health", { signal }),

  /** GET /metrics — process metrics snapshot (public). */
  metrics: (signal?: AbortSignal) => request<MetricsResponse>("/metrics", { signal }),

  /** GET /api/models — provider/model catalogue + agent tools + caller permissions. */
  models: (signal?: AbortSignal) => request<ModelsResponse>("/api/models", { signal }),

  /** GET /api/users — demo account directory (admin only). */
  users: (signal?: AbortSignal) => request<UsersResponse>("/api/users", { signal }),

  /** POST /api/chat — direct Model Gateway call (Day 1 path). */
  chat: (
    payload: { message: string; mode?: "auto" | "chat" | "agent"; model?: string | null },
    signal?: AbortSignal,
  ) => request<ChatResponse>("/api/chat", { method: "POST", body: payload, signal }),

  /** POST /api/agent/run — Agent Runtime: model → permission-checked tools → answer. */
  agentRun: (payload: { message: string; max_steps?: number | null }, signal?: AbortSignal) =>
    request<AgentRunResponse>("/api/agent/run", { method: "POST", body: payload, signal }),

  /** GET /api/knowledge/documents — ingested documents + chunk statistics. */
  knowledgeDocuments: (signal?: AbortSignal) =>
    request<DocumentsResponse>("/api/knowledge/documents", { signal }),

  /** POST /api/knowledge/search — cited retrieval (+ optional generated answer). */
  knowledgeSearch: (
    payload: { query: string; top_k?: number | null; include_answer?: boolean },
    signal?: AbortSignal,
  ) => request<SearchResponse>("/api/knowledge/search", { method: "POST", body: payload, signal }),

  /** POST /api/knowledge/ingest — rebuild the knowledge base (admin only). */
  knowledgeIngest: (
    payload: { path?: string | null; rebuild?: boolean } = {},
    signal?: AbortSignal,
  ) => request<IngestResponse>("/api/knowledge/ingest", { method: "POST", body: payload, signal }),

  /** GET /api/audit — paginated audit trail (admin + manager). */
  audit: (filters: AuditFilters = {}, signal?: AbortSignal) =>
    request<AuditListResponse>(`/api/audit${query({ ...filters })}`, { signal }),

  /** GET /api/audit/{request_id} — the whole trail of one run. */
  auditTrace: (requestId: string, signal?: AbortSignal) =>
    request<AuditListResponse>(`/api/audit/${encodeURIComponent(requestId)}`, { signal }),
};

export type Api = typeof api;

/** Narrow an unknown thrown value into the platform failure shape for the UI. */
export function asFailure(error: unknown): ApiFailure {
  if (error instanceof ApiRequestError) return error;
  const message = error instanceof Error ? error.message : String(error);
  return new ApiRequestError({
    status: -1,
    code: "UNKNOWN_ERROR",
    message,
    denied: false,
  });
}
