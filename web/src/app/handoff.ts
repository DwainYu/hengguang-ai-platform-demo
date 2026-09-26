/**
 * One deliberate cross-page hand-off: "show me this request_id in the Audit
 * trail". Kept in `sessionStorage` (not React state) so the Audit page can pick
 * it up on mount without a global store — it is a navigation hint, not data.
 */

const KEY = "hengguang.audit.request_id";

export function handoffRequest(requestId: string): void {
  window.sessionStorage.setItem(KEY, requestId);
}

/** Read and clear the handed-over request id (so a reload does not stick). */
export function takeHandoffRequest(): string | null {
  const value = window.sessionStorage.getItem(KEY);
  if (value) window.sessionStorage.removeItem(KEY);
  return value;
}
