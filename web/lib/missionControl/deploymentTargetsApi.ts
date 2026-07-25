/** Deployment target registry — Mission Control Engineering section. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type DeploymentTarget = {
  target_id: string;
  alias: string;
  aliases?: string[];
  repo: string;
  branch?: string;
  workspace_id?: string;
  local_path?: string;
  vercel_project?: string;
  railway_project?: string;
  railway_service?: string;
  railway_environment?: string;
  root_directory?: string;
  default_provider?: string;
  registered_at?: number;
  updated_at?: number;
};

export type DeploymentBinding = {
  binding_id: string;
  target_id: string;
  match?: {
    session_id?: string;
    user_id?: string;
    channel?: string;
  };
  priority?: number;
};

export type DeploymentTargetsListResponse = {
  ok: boolean;
  targets: DeploymentTarget[];
  bindings: DeploymentBinding[];
  default_target_id?: string;
};

export type DeploymentTargetResolution = {
  ok: boolean;
  source?: string;
  repo?: string;
  branch?: string;
  alias?: string;
  vercel_project?: string;
  railway_project?: string;
  blocker_code?: string;
  detail?: string;
};

export async function listDeploymentTargets(): Promise<DeploymentTargetsListResponse> {
  return mcFetch<DeploymentTargetsListResponse>("/api/v1/deployment-targets");
}

export async function registerDeploymentTarget(body: {
  alias: string;
  repo: string;
  branch?: string;
  vercel_project?: string;
  railway_project?: string;
  railway_service?: string;
  railway_environment?: string;
  root_directory?: string;
  local_path?: string;
  workspace_id?: string;
  confirm_production_binding?: boolean;
}): Promise<{ ok: boolean; target: DeploymentTarget }> {
  return mcFetch("/api/v1/deployment-targets/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function resolveDeploymentTarget(params: {
  text?: string;
  session_id?: string;
  workspace_hint?: string;
}): Promise<{ ok: boolean; resolution: DeploymentTargetResolution; report: string }> {
  const query = new URLSearchParams();
  if (params.text) query.set("text", params.text);
  if (params.session_id) query.set("session_id", params.session_id);
  if (params.workspace_hint) query.set("workspace_hint", params.workspace_hint);
  return mcFetch(`/api/v1/deployment-targets/resolve?${query.toString()}`);
}
