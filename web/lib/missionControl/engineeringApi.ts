/** Engineering + tunnel — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type EngineeringPreflightCard = {
  preflight_id?: string;
  job_id?: string;
  approval_status?: string;
  approval_required?: boolean;
  approved?: boolean;
  denied?: boolean;
  risk_tier?: string;
  target_workspace?: string;
  task?: { title?: string; problem_summary?: string; likely_cause?: string; kind?: string };
  patch_plan?: {
    affected_files?: string[];
    patch_summary?: string;
    validation_steps?: string[];
    rollback_strategy?: string;
  };
  patch_proposal?: {
    files_affected?: string[];
    unified_diffs?: { file?: string; diff?: string; lines_changed?: number }[];
    diff_intelligence?: { severity?: string; warnings?: string[]; summary?: string };
    blast_radius?: { surfaces?: string[] };
  };
  execution?: EngineeringExecution;
};

export type EngineeringExecution = {
  execution_id?: string;
  status?: string;
  branch?: string;
  patch_artifact_id?: string;
  diff_intelligence?: { severity?: string; summary?: string };
  pr_draft?: { title?: string; status?: string; body?: string; governance_statement?: string };
  validation?: { validation_status?: string; pass_count?: number; fail_count?: number; ok?: boolean };
  proposal_only?: boolean;
  merge_enabled?: boolean;
  audit?: { preflight_id?: string; auto_merge?: boolean };
};

export type MutationWorkspace = {
  workspace_id?: string;
  branch?: string;
  files_modified?: string[];
  validation_status?: string;
  rollback_snapshot?: string;
  sandbox_path?: string;
};

export type PatchArtifact = {
  artifact_id?: string;
  preflight_id?: string;
  execution_id?: string;
  unified_diffs?: { file?: string; diff?: string; lines_changed?: number }[];
  diff_intelligence?: { severity?: string; warnings?: string[]; summary?: string };
};

export type RollbackSnapshot = {
  snapshot_id?: string;
  workspace_id?: string;
  branch?: string;
  files_modified?: string[];
  created_at?: number;
};

export type EngineeringStateResponse = {
  ok: boolean;
  pending_preflights?: EngineeringPreflightCard[];
  approved_preflights?: EngineeringPreflightCard[];
  mutation_workspaces?: MutationWorkspace[];
  executions?: EngineeringExecution[];
  pr_drafts?: { draft_id?: string; title?: string; body?: string; status?: string; governance_statement?: string }[];
  patch_artifacts?: PatchArtifact[];
  validations?: { execution_id?: string; preflight_id?: string; validation?: EngineeringExecution["validation"] }[];
  rollback_snapshots?: RollbackSnapshot[];
  engineering_memory?: { total_events?: number; recent_failures?: unknown[] };
  reality_loop?: {
    recurring_patterns?: string[];
    anomalies?: string[];
    trends?: string[];
  };
};

export type TunnelStatusResponse = {
  ok: boolean;
  tunnel?: {
    provider?: string;
    status?: string;
    local_port?: number;
    public_url?: string;
    webhook_url?: string;
    telegram_webhook_status?: string;
    last_started_at?: number;
    last_error?: string;
    enabled?: boolean;
  };
  telegram?: {
    enabled?: boolean;
    configured?: boolean;
    webhook?: { url?: string };
  };
};

export const fetchEngineeringState = () => mcFetch<EngineeringStateResponse>("/api/v1/engineering/state");

export const fetchEngineeringDiff = (artifactId: string) =>
  mcFetch<{ ok: boolean; artifact?: PatchArtifact }>(`/api/v1/engineering/diffs/${artifactId}`);

export const fetchEngineeringPrDrafts = () =>
  mcFetch<{ ok: boolean; drafts?: EngineeringStateResponse["pr_drafts"] }>("/api/v1/engineering/pr-drafts");

export const fetchEngineeringValidations = () =>
  mcFetch<{ ok: boolean; validations?: EngineeringStateResponse["validations"] }>("/api/v1/engineering/validations");

export const fetchRollbackSnapshots = () =>
  mcFetch<{ ok: boolean; snapshots?: RollbackSnapshot[] }>("/api/v1/engineering/rollback-snapshots");

export const approveEngineeringPreflight = (preflightId: string) =>
  mcFetch<{ ok: boolean; preflight?: EngineeringPreflightCard; execution?: EngineeringExecution }>(
    `/api/v1/engineering/preflights/${preflightId}/approve`,
    { method: "POST" },
  );

export const denyEngineeringPreflight = (preflightId: string, reason = "") =>
  mcFetch<{ ok: boolean }>(`/api/v1/engineering/preflights/${preflightId}/deny`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });

export const fetchRealityLoop = () =>
  mcFetch<{ ok: boolean; report?: string; scan?: EngineeringStateResponse["reality_loop"] }>(
    "/api/v1/engineering/reality-loop",
  );

export const fetchTunnelStatus = () => mcFetch<TunnelStatusResponse>("/api/v1/runtime/tunnel/status");

export const startTunnel = () => mcFetch<TunnelStatusResponse>("/api/v1/runtime/tunnel/start", { method: "POST" });

export const stopTunnel = () => mcFetch<TunnelStatusResponse>("/api/v1/runtime/tunnel/stop", { method: "POST" });

export const restartTunnel = () => mcFetch<TunnelStatusResponse>("/api/v1/runtime/tunnel/restart", { method: "POST" });
