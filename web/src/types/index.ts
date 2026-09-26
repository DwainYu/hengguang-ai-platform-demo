/**
 * TypeScript mirrors of the FastAPI response models (Day 5).
 *
 * Every shape here is taken from the real backend schemas in `app/api/*` — the
 * front end must not invent fields. `null` and optional are used exactly where
 * the backend sends them.
 */

/** Error envelope of `app/api/errors.py`: `{detail, request_id, error}`. */
export interface ApiErrorBody {
  detail: string;
  request_id: string;
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface HealthResponse {
  status: "ok" | string;
  version: string;
  database: {
    configured: boolean;
    initialized: boolean;
    tables: number;
    seeded: boolean;
    rows: Record<string, number>;
  };
  request_count: number;
  request_id: string;
}

export interface ModelInfo {
  provider: string;
  model: string;
  available: boolean;
  default: boolean;
  kind: "chat" | "embedding" | string;
}

export interface ModelsResponse {
  request_id: string;
  models: ModelInfo[];
  agent: {
    tools: string[];
    allowed_tools: string[];
    max_steps: number;
    max_tool_calls: number;
  };
  permissions: string[];
}

export interface MetricsResponse {
  request_count: number;
  success_count: number;
  error_count: number;
  avg_latency_ms: number;
  max_latency_ms: number;
  requests_by_status_class: Record<string, number>;
  requests_by_endpoint: Record<string, { count: number; avg_latency_ms: number }>;
  error_by_code: Record<string, number>;
  tool_call_count: number;
  tool_error_count: number;
  permission_denied_count: number;
  agent_run_count: number;
  agent_runs_by_status: Record<string, number>;
  audit_write_count: number;
  uptime_seconds: number;
  app: { version: string; provider: string };
  endpoint: string;
  request_id: string;
}

export interface AgentToolCall {
  name: string;
  arguments: Record<string, unknown>;
  success: boolean | null;
  error: string | null;
  error_code: string | null;
  operation: string | null;
  result_count: number | null;
}

export interface AgentSource {
  index: number | null;
  document_id: string;
  title: string;
  section: string | null;
  page: number | null;
  source: string;
  url: string;
  score: number | null;
  citation: string;
}

export type TraceStepType = "llm" | "tool_call" | "final" | "stopped" | string;

export interface AgentTraceStep {
  step: number;
  type: TraceStepType;
  tool: string | null;
  latency_ms: number;
  detail: string | null;
}

export type AgentRunStatus = "completed" | "max_steps" | "max_tool_calls" | string;

export interface AgentRunResponse {
  request_id: string;
  answer: string;
  model: string;
  provider: string;
  steps: number;
  status: AgentRunStatus;
  latency_ms: number;
  user: string;
  role: string;
  tool_calls: AgentToolCall[];
  sources: AgentSource[];
  trace: AgentTraceStep[];
}

export interface ChatResponse {
  request_id: string;
  answer: string;
  mode: string;
  model: string;
  provider: string;
  latency_ms: number;
  user: string;
  role: string;
  sources: Record<string, unknown>[];
  tool_calls: Record<string, unknown>[];
}

export interface DocumentSummary {
  document_id: string;
  title: string;
  source: string;
  url: string;
  published_at: string;
  chunks: number;
  chars: number;
  sections: string[];
}

export interface DocumentsResponse {
  request_id: string;
  documents: DocumentSummary[];
  total_documents: number;
  total_chunks: number;
}

export interface IngestResponse {
  request_id: string;
  documents: number;
  chunks: number;
  status: string;
  skipped: string[];
  errors: string[];
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  title: string;
  content: string;
  score: number;
  section: string | null;
  page: number | null;
  source: string;
  url: string;
  published_at: string;
  position: number;
  citation: string;
}

export interface Citation {
  index: number;
  document_id: string;
  title: string;
  section: string | null;
  page: number | null;
  source: string;
  url: string;
  published_at: string;
  score: number;
}

export interface SearchResponse {
  request_id: string;
  query: string;
  count: number;
  results: SearchResult[];
  citations: Citation[];
  answer: string | null;
  model: string;
  provider: string;
  latency_ms: number;
}

export interface AuditEntry {
  id: number;
  request_id: string;
  user_id: number | null;
  username: string;
  role: string;
  action: string;
  endpoint: string | null;
  operation: string;
  tool: string | null;
  model: string | null;
  mode: string | null;
  input_summary: Record<string, unknown>;
  status: "success" | "error" | "denied" | "unauthenticated" | "not_found" | "conflict" | string;
  latency_ms: number | null;
  created_at: string;
}

export interface AuditListResponse {
  request_id: string;
  items: AuditEntry[];
  page: number;
  page_size: number;
  total: number;
  viewer?: { username: string; role: string };
  query_request_id?: string;
}

export interface DemoUserEntry {
  id: string;
  username: string;
  role: string;
  permissions: string[];
}

export interface UsersResponse {
  request_id: string;
  users: DemoUserEntry[];
  permission_roles: Record<string, string[]>;
}

/** One entry of the local playground conversation log. */
export interface PlaygroundTurn {
  id: string;
  question: string;
  result: AgentRunResponse | null;
  error: ApiFailure | null;
  started_at: string;
}

/** Normalised API failure produced by `services/api.ts`. */
export interface ApiFailure {
  status: number;
  code: string;
  message: string;
  request_id: string;
  details: Record<string, unknown>;
  /** True for 401/403: the caller is shown "Permission denied", not a stack trace. */
  denied: boolean;
}

/** Demo roles understood by the platform (`app/auth/auth.py`). */
export type DemoRole = "admin" | "manager" | "operator";

export interface DemoIdentity {
  role: DemoRole;
  username: string;
  token: string;
  label: string;
}
