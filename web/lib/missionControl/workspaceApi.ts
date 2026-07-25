/** Workspace runtime — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type WorkspaceRuntimeArtifact = {
  artifact_id?: string;
  artifact_type?: string;
  workspace_id?: string | null;
  summary?: string;
  created_at?: number;
  payload?: Record<string, unknown>;
};

export type TerminalPreflight = {
  preflight_id?: string;
  status?: string;
  command?: string;
  cwd?: string;
  approval_required?: boolean;
  execution_enabled?: boolean;
  policy?: { allowed?: boolean; reason?: string; error?: string };
  denial_artifact_id?: string;
};

export type WorkspaceRuntimeState = {
  ok: boolean;
  status?: { workspace_id?: string; path?: string; registered?: boolean };
  runtime?: {
    workspaces?: unknown[];
    sessions?: unknown[];
    artifacts?: WorkspaceRuntimeArtifact[];
    audit?: unknown[];
    memory?: Record<string, unknown>;
    desktop?: { windows?: unknown; processes?: unknown };
    autonomous_execution_blocked?: boolean;
  };
};

export const fetchWorkspaceRuntimeStatus = (hint?: string) =>
  mcFetch<WorkspaceRuntimeState>(`/api/v1/workspace/status${hint ? `?hint=${encodeURIComponent(hint)}` : ""}`);

export const fetchWorkspaceWindows = () => mcFetch<{ ok: boolean; windows?: unknown }>("/api/v1/workspace/windows");

export const fetchWorkspaceProcesses = () => mcFetch<{ ok: boolean; processes?: unknown }>("/api/v1/workspace/processes");

export const fetchWorkspaceSessions = () =>
  mcFetch<{ ok: boolean; sessions?: unknown[]; terminal_preflights?: TerminalPreflight[] }>("/api/v1/workspace/sessions");

export const fetchWorkspaceRuntimeArtifacts = () =>
  mcFetch<{ ok: boolean; artifacts?: WorkspaceRuntimeArtifact[] }>("/api/v1/workspace/artifacts");

export const fetchWorkspaceAudit = () => mcFetch<{ ok: boolean; audit?: unknown[] }>("/api/v1/workspace/audit");

export const fetchWorkspaceMemory = () => mcFetch<{ ok: boolean; memory?: Record<string, unknown> }>("/api/v1/workspace/memory");

export const terminalPreflight = (command: string, workspaceHint = "aethos") =>
  mcFetch<{ ok: boolean; preflight?: TerminalPreflight }>("/api/v1/workspace/terminal/preflight", {
    method: "POST",
    body: JSON.stringify({ command, workspace_hint: workspaceHint }),
  });

export const terminalExecute = (preflightId: string) =>
  mcFetch<{ ok: boolean; execution?: { output?: string; artifact_id?: string; status?: string } }>(
    "/api/v1/workspace/terminal/execute",
    { method: "POST", body: JSON.stringify({ preflight_id: preflightId, approved: true }) },
  );

export const runWorkspaceDiagnostics = (userRequest: string, hint = "aethos") =>
  mcFetch<{ ok: boolean; replay_id?: string; artifact_id?: string }>(
    `/api/v1/workspace/diagnostics?user_request=${encodeURIComponent(userRequest)}&hint=${encodeURIComponent(hint)}`,
    { method: "POST" },
  );
