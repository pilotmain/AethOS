/** Credential center — provider auth validation state (Phase 9.6.6 / 9.8B.3). */

import { mcFetch } from "@/lib/missionControl/fetch";
import type { CredentialVaultDiagnostics } from "@/lib/missionControl/connectionsApi";

export type CredentialCenterProvider = {
  provider: string;
  status: string;
  credential_state?: string;
  last_validated_at?: number | null;
  last_tested_at?: number | null;
  scope?: string;
  masked_preview?: string | null;
  credential_id?: string | null;
  credential_count?: number;
  validation_diagnostics?: Record<string, unknown>;
  failure_class?: string | null;
  auth_source?: string;
  decryptable?: boolean;
  runtime_usable?: boolean;
  actions_allowed?: {
    revalidate?: boolean;
    reconnect?: boolean;
    repair?: boolean;
  };
};

export type CredentialCenterResponse = {
  ok: boolean;
  providers: CredentialCenterProvider[];
  vault?: CredentialVaultDiagnostics;
  hydration?: Record<string, unknown> | null;
};

export async function fetchCredentialCenter(): Promise<CredentialCenterResponse> {
  return mcFetch("/api/v1/connections/credential-center");
}

export async function hydrateCredentials(): Promise<{ ok: boolean; hydration?: Record<string, unknown> }> {
  return mcFetch("/api/v1/connections/hydrate", { method: "POST", body: "{}" });
}

export async function revalidateCredential(
  provider: string,
  credentialId: string,
): Promise<{ ok: boolean; validation?: { ok?: boolean; validation_status?: string } }> {
  return mcFetch(
    `/api/v1/connections/${encodeURIComponent(provider)}/credentials/${encodeURIComponent(credentialId)}/revalidate`,
    { method: "POST", body: "{}" },
  );
}

export async function repairCredential(
  provider: string,
  token: string,
): Promise<{ ok: boolean; repair?: Record<string, unknown> }> {
  return mcFetch(`/api/v1/connections/${encodeURIComponent(provider)}/repair`, {
    method: "POST",
    body: JSON.stringify({ type: "api_token", token }),
  });
}

export async function rotateCredential(
  provider: string,
  credentialId: string,
  token: string,
): Promise<{ ok: boolean; rotated?: boolean }> {
  return mcFetch(
    `/api/v1/connections/${encodeURIComponent(provider)}/credentials/${encodeURIComponent(credentialId)}/rotate`,
    {
      method: "POST",
      body: JSON.stringify({ type: "api_token", token }),
    },
  );
}

export type DeploymentEnvVarRow = {
  name: string;
  purpose: string;
  resolved: boolean;
  source?: string;
  resolution_source_label?: string;
};

export type DeploymentEnvContext = {
  ok: boolean;
  target_key: string;
  repo: string;
  project: string;
  environment: string;
  service_name: string;
  required: DeploymentEnvVarRow[];
  resolved_names: string[];
  missing_names: string[];
  stored_names: string[];
  ui_surface: string;
  credential_center_path: string;
  missing_count: number;
  resolved_count: number;
};

export async function fetchDeploymentEnvContext(params: {
  repo?: string;
  project?: string;
  environment?: string;
  service_name?: string;
  target_key?: string;
  required_names?: string[];
}): Promise<DeploymentEnvContext> {
  const qs = new URLSearchParams();
  if (params.repo) qs.set("repo", params.repo);
  if (params.project) qs.set("project", params.project);
  if (params.environment) qs.set("environment", params.environment);
  if (params.service_name) qs.set("service_name", params.service_name);
  if (params.target_key) qs.set("target_key", params.target_key);
  if (params.required_names?.length) qs.set("required_names", params.required_names.join(","));
  return mcFetch(`/api/v1/connections/deployment-env-values/context?${qs.toString()}`);
}

export async function storeDeploymentEnvValues(body: {
  repo?: string;
  project?: string;
  environment?: string;
  service_name?: string;
  target_key?: string;
  values: Record<string, string>;
}): Promise<{ ok: boolean; target_key?: string; registered_names?: string[]; count?: number }> {
  return mcFetch("/api/v1/connections/deployment-env-values", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
