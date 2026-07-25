/** Mission Control connection settings API. */

import { apiBase } from "@/lib/api";
import { mcFetch } from "@/lib/missionControl/fetch";
import {
  formatConnectionSaveError,
  parseConnectionErrorPayload,
} from "@/lib/missionControl/connectionErrors";

export type ConnectionMethods = {
  api_token: string;
  browser_session: string;
  cli_auth: string;
  username_password: string;
};

export type CredentialVaultDiagnostics = {
  available?: boolean;
  backend?: string;
  credentials_dir?: string;
  credentials_dir_exists?: boolean;
  can_write?: boolean;
  dependencies?: { cryptography?: string; keyring?: string };
};

export type CredentialRecord = {
  credential_id: string;
  provider: string;
  type: string;
  label: string;
  masked_identifier?: string;
  last_test_ok?: boolean | null;
  revoked?: boolean;
};

export type ProviderConnection = {
  provider: string;
  preferred_method: string;
  connected_methods: ConnectionMethods;
  credentials: CredentialRecord[];
  credential_vault?: CredentialVaultDiagnostics;
};

export type ConnectionsResponse = {
  providers: Record<string, ProviderConnection>;
  count: number;
  credential_vault?: CredentialVaultDiagnostics;
};

export function providerCredentialsSaveUrl(provider: string): string {
  return `${apiBase()}/api/v1/connections/${encodeURIComponent(provider)}/credentials`;
}

export function vercelCredentialsSaveUrl(): string {
  return providerCredentialsSaveUrl("vercel");
}

export async function fetchConnections(): Promise<ConnectionsResponse> {
  return mcFetch("/api/v1/connections");
}

export async function fetchConnectionDiagnostics(): Promise<{ credential_vault: CredentialVaultDiagnostics }> {
  return mcFetch("/api/v1/connections/diagnostics");
}

export async function fetchProviderConnection(provider: string): Promise<ProviderConnection> {
  return mcFetch(`/api/v1/connections/${encodeURIComponent(provider)}`);
}

export type StoreTokenResult = {
  ok: boolean;
  credential?: CredentialRecord;
  test?: { ok?: boolean; detail?: string };
  code?: string;
  detail?: string;
};

export async function storeProviderApiToken(
  provider: string,
  body: { label: string; token: string },
): Promise<StoreTokenResult> {
  const requestUrl = providerCredentialsSaveUrl(provider);
  try {
    const res = await fetch(requestUrl, {
      method: "POST",
      cache: "no-store",
      credentials: "include",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "api_token",
        label: body.label,
        token: body.token,
      }),
    });
    const text = await res.text();
    let data: StoreTokenResult & { code?: string; detail?: string } = { ok: false };
    try {
      data = JSON.parse(text) as StoreTokenResult & { code?: string; detail?: string };
    } catch {
      data = { ok: false, detail: text || `HTTP ${res.status}` };
    }
    if (!res.ok || data.ok === false) {
      const parsed = parseConnectionErrorPayload(text);
      const err = new Error(parsed.detail || text || `HTTP ${res.status}`);
      (err as Error & { code?: string; status?: number }).code = parsed.code || data.code;
      (err as Error & { status?: number }).status = res.status;
      throw err;
    }
    return data;
  } catch (err) {
    const formatted = formatConnectionSaveError(err, {
      requestUrl,
      httpStatus: (err as Error & { status?: number }).status,
      errorCode: (err as Error & { code?: string }).code,
    });
    const wrapped = new Error(formatted.message);
    (wrapped as Error & { debug?: unknown }).debug = formatted.debug;
    throw wrapped;
  }
}

export async function storeVercelApiToken(body: {
  label: string;
  token: string;
}): Promise<StoreTokenResult> {
  return storeProviderApiToken("vercel", body);
}

export async function testCredential(
  provider: string,
  credentialId: string,
): Promise<{ test: { ok?: boolean; detail?: string; sample_projects?: string[] } }> {
  return mcFetch(
    `/api/v1/connections/${encodeURIComponent(provider)}/credentials/${encodeURIComponent(credentialId)}/test`,
    { method: "POST", body: "{}" },
  );
}

export async function revokeCredential(provider: string, credentialId: string): Promise<{ revoked: boolean }> {
  return mcFetch(
    `/api/v1/connections/${encodeURIComponent(provider)}/credentials/${encodeURIComponent(credentialId)}/revoke`,
    { method: "POST", body: "{}" },
  );
}

export async function setPreferredAuth(
  provider: string,
  preferredMethod: string,
): Promise<{ preferred_method: string }> {
  return mcFetch(`/api/v1/connections/${encodeURIComponent(provider)}/preferred-auth`, {
    method: "POST",
    body: JSON.stringify({ preferred_method: preferredMethod }),
  });
}

export function methodLabel(value: string): string {
  const labels: Record<string, string> = {
    configured: "Configured",
    saved: "Saved",
    expired: "Expired",
    missing: "Missing",
    detected: "Detected",
    not_detected: "Not detected",
    revoked: "Revoked",
  };
  return labels[value] ?? value.replace(/_/g, " ");
}

export function vaultReadyLabel(vault?: CredentialVaultDiagnostics): string {
  if (!vault) return "Unknown";
  if (vault.available) return `Ready (${vault.backend ?? "vault"})`;
  const crypto = vault.dependencies?.cryptography;
  if (crypto === "missing") return "Unavailable — install `cryptography` in API venv";
  if (!vault.can_write) return "Unavailable — credentials directory not writable";
  return "Unavailable";
}
