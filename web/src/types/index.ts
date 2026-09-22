export interface Source {
  document_id: string;
  title: string;
  page?: number;
  section?: string;
  score?: number;
}

export interface ToolCall {
  tool: string;
  status: string;
}

export interface ChatResponse {
  request_id: string;
  answer: string;
  mode: string;
  model: string;
  sources: Source[];
  tool_calls: ToolCall[];
  latency_ms: number;
}
