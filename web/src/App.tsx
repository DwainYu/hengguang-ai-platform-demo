import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Workspace } from "./pages/Workspace";
import { Knowledge } from "./pages/Knowledge";

type Page = "dashboard" | "workspace" | "knowledge";

export function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app">
      <h1>Hengguang AI Platform</h1>
      <nav className="tabs">
        <button className={page === "dashboard" ? "active" : ""} onClick={() => setPage("dashboard")}>
          Dashboard
        </button>
        <button className={page === "workspace" ? "active" : ""} onClick={() => setPage("workspace")}>
          AI Workspace
        </button>
        <button className={page === "knowledge" ? "active" : ""} onClick={() => setPage("knowledge")}>
          Knowledge
        </button>
      </nav>
      {page === "dashboard" && <Dashboard />}
      {page === "workspace" && <Workspace />}
      {page === "knowledge" && <Knowledge />}
    </div>
  );
}
