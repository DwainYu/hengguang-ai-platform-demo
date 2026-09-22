/** Minimal typed API client for the platform backend. */

const BASE = "";

export async function getHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${BASE}/health`);
  return (await res.json()) as { status: string; version: string };
}

export async function postChat(body: {
  message: string;
  mode?: "auto" | "chat" | "agent";
  model?: string | null;
  token?: string;
}): Promise<unknown> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(body.token ? { Authorization: `Bearer ${body.token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  return res.json();
}
