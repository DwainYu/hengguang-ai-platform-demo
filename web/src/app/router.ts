/**
 * Tiny hash router (no dependency): `#/`, `#/agent`, `#/knowledge`, `#/audit`,
 * `#/settings`. Hash routing keeps the static container config trivial (one
 * index.html, no server rewrite rules) while still giving shareable deep links
 * for the demo, which is what the interview walkthrough needs.
 */

import { useEffect, useState } from "react";

export type RoutePath = "/" | "/agent" | "/knowledge" | "/audit" | "/settings";

export const ROUTES: { path: RoutePath; label: string; hint: string }[] = [
  { path: "/", label: "Dashboard", hint: "平台状态与指标" },
  { path: "/agent", label: "Agent Playground", hint: "Agent · Tool · Trace" },
  { path: "/knowledge", label: "Knowledge", hint: "RAG 知识库与引用" },
  { path: "/audit", label: "Audit", hint: "审计链路与 request_id" },
  { path: "/settings", label: "Settings", hint: "身份、模型与权限矩阵" },
];

function currentPath(): RoutePath {
  const raw = window.location.hash.replace(/^#/, "") || "/";
  const known = ROUTES.find((route) => route.path === raw);
  return known ? known.path : "/";
}

export function navigate(path: RoutePath): void {
  if (currentPath() === path) return;
  window.location.hash = path;
}

export function useRoute(): RoutePath {
  const [path, setPath] = useState<RoutePath>(currentPath);

  useEffect(() => {
    const onChange = () => setPath(currentPath());
    window.addEventListener("hashchange", onChange);
    if (!window.location.hash) window.location.hash = "/";
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  return path;
}
