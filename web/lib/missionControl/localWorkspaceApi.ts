/** Local workspace engineering intelligence — Mission Control Engineering section. */

import { mcFetch } from "@/lib/missionControl/fetch";

export const WORKSPACE_ARTIFACT_PATH_WARNING =
  "This looks like a generated mutation workspace, not a project root. Use the real repo root instead.";

export function validateWorkspaceRegistrationPath(path: string): string | null {
  const normalized = path.trim().replace(/\\/g, "/");
  if (!normalized) return null;
  if (/data\/agent_artifacts\/mutation_workspaces\//i.test(normalized)) {
    return WORKSPACE_ARTIFACT_PATH_WARNING;
  }
  return null;
}

export type WorkspaceStack = {
  badges?: string[];
  package_managers?: string[];
  languages?: string[];
  ci?: string[];
  docker?: boolean;
};

export type WorkspaceRecord = {
  workspace_id: string;
  name: string;
  path: string;
  source?: "github" | "local";
  repository?: string;
  remote_origin?: string | null;
  default_branch?: string | null;
  stack?: WorkspaceStack;
  registered_at?: number;
  last_scan_at?: number;
  health_state?: string;
};

export type WorkspaceArtifact = {
  artifact_id: string;
  artifact_type: string;
  workspace_id?: string | null;
  repo_path?: string;
  created_at?: number;
  summary?: string;
};

export type EngineeringMemory = {
  events?: Array<{
    at?: number;
    event?: string;
    workspace_id?: string | null;
    repo_path?: string;
    detail?: string;
  }>;
  repos?: Record<string, unknown>;
  updated_at?: number | null;
};

export type PortfolioProject = {
  name: string;
  path: string;
  remote_origin?: string | null;
  default_branch?: string | null;
  discovered_at?: number;
};

export type PortfolioConfig = {
  portfolio_root?: string;
  max_scan_depth?: number;
  max_projects?: number;
  last_discovered_at?: number | null;
  discovered_count?: number;
  discovered?: PortfolioProject[];
};

export type WorkspacesListResponse = {
  ok: boolean;
  hosted?: boolean;
  deployment_mode?: string;
  workspaces: WorkspaceRecord[];
  portfolio?: PortfolioConfig;
  artifacts: WorkspaceArtifact[];
  engineering_memory: EngineeringMemory;
};

export const fetchEngineeringContext = (sessionId = "default") =>
  mcFetch<{
    ok: boolean;
    active_workspace?: { name?: string; path?: string; workspace_id?: string; default_branch?: string };
    git?: { branch?: string; modified_count?: number; untracked_count?: number; ahead?: number; behind?: number };
    architecture_summary?: string | null;
    dependency_severity?: string | null;
    engineering_memory_events?: Array<{ event?: string; detail?: string; at?: number }>;
    workspaces_count?: number;
  }>(`/api/v1/workspaces/context?session_id=${encodeURIComponent(sessionId)}`);

export const fetchWorkspaces = () => mcFetch<WorkspacesListResponse>("/api/v1/workspaces");

export const registerWorkspace = (path: string, name = "") =>
  mcFetch<{ ok: boolean; workspace: WorkspaceRecord; scan?: unknown; artifact?: WorkspaceArtifact }>(
    "/api/v1/workspaces/register",
    { method: "POST", body: JSON.stringify({ path, name }) },
  );

export const registerGithubWorkspace = (repository: string, branch = "", name = "") =>
  mcFetch<{ ok: boolean; workspace: WorkspaceRecord }>("/api/v1/workspaces/github/register", {
    method: "POST",
    body: JSON.stringify({ repository, branch, name }),
  });

export const fetchWorkspaceStatus = (workspaceId: string) =>
  mcFetch<{ ok: boolean; workspace: WorkspaceRecord; report?: string; git?: Record<string, unknown> }>(
    `/api/v1/workspaces/${encodeURIComponent(workspaceId)}/status`,
  );

export const fetchWorkspaceArchitecture = (workspaceId: string) =>
  mcFetch<{ ok: boolean; workspace: WorkspaceRecord; report?: string; analysis?: Record<string, unknown> }>(
    `/api/v1/workspaces/${encodeURIComponent(workspaceId)}/architecture`,
  );

export const fetchWorkspaceDependencies = (workspaceId: string) =>
  mcFetch<{ ok: boolean; workspace: WorkspaceRecord; report?: string; analysis?: Record<string, unknown> }>(
    `/api/v1/workspaces/${encodeURIComponent(workspaceId)}/dependencies`,
  );

export const fetchWorkspaceTests = (workspaceId: string) =>
  mcFetch<{ ok: boolean; workspace: WorkspaceRecord; tests?: Record<string, unknown> }>(
    `/api/v1/workspaces/${encodeURIComponent(workspaceId)}/tests`,
  );

export const fetchWorkspaceArtifacts = (limit = 40) =>
  mcFetch<{ ok: boolean; artifacts: WorkspaceArtifact[] }>(
    `/api/v1/workspaces/artifacts?limit=${limit}`,
  );

export const fetchWorkspaceArtifact = (artifactId: string) =>
  mcFetch<{ ok: boolean; artifact: WorkspaceArtifact & { payload?: unknown } }>(
    `/api/v1/workspaces/artifacts/${encodeURIComponent(artifactId)}`,
  );

export const fetchPortfolio = () =>
  mcFetch<{ ok: boolean; portfolio: PortfolioConfig }>("/api/v1/workspaces/portfolio");

export const setPortfolioRoot = (path: string, maxScanDepth = 4, maxProjects = 100) =>
  mcFetch<{ ok: boolean; portfolio: PortfolioConfig }>("/api/v1/workspaces/portfolio", {
    method: "POST",
    body: JSON.stringify({ path, max_scan_depth: maxScanDepth, max_projects: maxProjects }),
  });

export const discoverPortfolioProjects = (autoRegister = false) =>
  mcFetch<{
    ok: boolean;
    portfolio_root?: string;
    project_count?: number;
    projects?: PortfolioProject[];
    auto_registered?: number;
  }>("/api/v1/workspaces/portfolio/discover", {
    method: "POST",
    body: JSON.stringify({ auto_register: autoRegister, rescan: true }),
  });
