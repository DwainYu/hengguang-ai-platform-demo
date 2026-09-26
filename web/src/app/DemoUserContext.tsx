/**
 * Demo identity context (Day 5 UI).
 *
 * The console talks to the backend as one of the three fixed demo accounts of
 * Day 4 (`app/auth/auth.py`). Switching the role only changes *which bearer
 * token the UI sends* — everything here is UX (which buttons to draw, which
 * badge to show), never a security boundary: the API re-checks the permission
 * and answers 403 / tool-level `PERMISSION_DENIED` no matter what the UI does.
 */

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { DEMO_TOKENS, setApiToken } from "../services/api";
import type { DemoIdentity, DemoRole } from "../types";

export const DEMO_IDENTITIES: Record<DemoRole, DemoIdentity> = {
  admin: { role: "admin", username: "admin_demo", token: DEMO_TOKENS.admin, label: "Admin" },
  manager: {
    role: "manager",
    username: "manager_demo",
    token: DEMO_TOKENS.manager,
    label: "Manager",
  },
  operator: {
    role: "operator",
    username: "operator_demo",
    token: DEMO_TOKENS.operator,
    label: "Operator",
  },
};

export const DEMO_ROLE_ORDER: DemoRole[] = ["admin", "manager", "operator"];

/** Capability notes per role — mirrors `ROLE_PERMISSIONS`, for labelling only. */
export const ROLE_CAPABILITIES: Record<DemoRole, string[]> = {
  admin: [
    "全部 API 权限（含 knowledge:ingest / users:manage）",
    "audit:read：可查看审计链路",
    "tool:erp / tool:safety / tool:knowledge 全部可用",
  ],
  manager: [
    "agent:run / chat:run / knowledge:query",
    "audit:read：可查看审计链路",
    "tool:erp / tool:safety / tool:knowledge 全部可用",
  ],
  operator: [
    "agent:run / chat:run / knowledge:query",
    "无 audit:read → 审计页面 403",
    "无 tool:erp → ERP 工具返回 PERMISSION_DENIED",
  ],
};

const STORAGE_KEY = "hengguang.demo.role";

function readStoredRole(): DemoRole {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === "admin" || stored === "manager" || stored === "operator" ? stored : "manager";
}

export interface DemoUserValue {
  role: DemoRole;
  identity: DemoIdentity;
  setRole: (role: DemoRole) => void;
  /** Bumped on every switch so role-scoped panels can refetch. */
  revision: number;
}

const DemoUserContext = createContext<DemoUserValue | null>(null);

export function DemoUserProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<DemoRole>(readStoredRole);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    setApiToken(DEMO_IDENTITIES[role].token);
    window.localStorage.setItem(STORAGE_KEY, role);
  }, [role]);

  const setRole = useCallback((next: DemoRole) => {
    setApiToken(DEMO_IDENTITIES[next].token);
    setRoleState(next);
    setRevision((value) => value + 1);
  }, []);

  return (
    <DemoUserContext.Provider
      value={{ role, identity: DEMO_IDENTITIES[role], setRole, revision }}
    >
      {children}
    </DemoUserContext.Provider>
  );
}

export function useDemoUser(): DemoUserValue {
  const value = useContext(DemoUserContext);
  if (!value) throw new Error("useDemoUser must be used inside <DemoUserProvider>");
  return value;
}
