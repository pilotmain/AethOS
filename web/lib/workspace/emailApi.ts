/** Workspace suite — Email triage + per-tenant IMAP credentials (vault-backed). */

import { apiBase, apiFetch } from "@/lib/api";
import type { CredentialRecord, CredentialVaultDiagnostics } from "@/lib/missionControl/connectionsApi";

export type TriagedMessage = {
  uid: string;
  subject: string;
  from: string;
  snippet: string;
  urgency: "high" | "normal";
  tags: string[];
  spam: boolean;
  summary: string;
};

export type TriageResponse = {
  ok: boolean;
  error?: string;
  hint?: string;
  message_count?: number;
  readonly?: boolean;
  messages: TriagedMessage[];
};

export type EmailDraft = {
  id: string;
  to: string;
  subject: string;
  body: string;
  status: string;
  sent: boolean;
  created_at?: number;
};

export type EmailCredentialField = {
  id: string;
  label: string;
  secret: boolean;
  required: boolean;
  placeholder?: string;
  help?: string;
};

export type EmailCredentialSchema = {
  service_id: string;
  label: string;
  primary_field: string;
  default_label: string;
  description?: string;
  fields: EmailCredentialField[];
};

export type EmailConnection = {
  ok: boolean;
  service: string;
  supports_credentials: boolean;
  schema?: EmailCredentialSchema | null;
  configured: boolean;
  credentials: CredentialRecord[];
  credential_vault?: CredentialVaultDiagnostics;
};

const base = () => `${apiBase()}/api/v1/human/workspace/email`;

export async function fetchEmailConnection(): Promise<EmailConnection> {
  const res = await apiFetch(`${base()}/connection`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`http_${res.status}`);
  return res.json();
}

export async function storeEmailCredentials(body: {
  label: string;
  fields: Record<string, string>;
}): Promise<{ ok: boolean; credential?: CredentialRecord; test?: { ok?: boolean; detail?: string } }> {
  const res = await apiFetch(`${base()}/credentials`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ label: body.label, fields: body.fields }),
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(detail.detail || `http_${res.status}`);
  }
  return res.json();
}

export async function testEmailCredential(credentialId: string): Promise<{ ok: boolean; test?: { ok?: boolean; detail?: string } }> {
  const res = await apiFetch(`${base()}/credentials/${encodeURIComponent(credentialId)}/test`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`http_${res.status}`);
  return res.json();
}

export async function revokeEmailCredential(credentialId: string): Promise<{ ok: boolean }> {
  const res = await apiFetch(`${base()}/credentials/${encodeURIComponent(credentialId)}/revoke`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`http_${res.status}`);
  return res.json();
}

export async function triageInbox(limit = 20): Promise<TriageResponse> {
  const res = await apiFetch(`${base()}/triage?limit=${limit}`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}`, messages: [] };
  return res.json();
}

export async function listDrafts(limit = 50): Promise<{ ok: boolean; error?: string; drafts: EmailDraft[] }> {
  const res = await apiFetch(`${base()}/drafts?limit=${limit}`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}`, drafts: [] };
  return res.json();
}

export async function createDraft(input: { to: string; subject?: string; body: string }): Promise<{ ok: boolean; error?: string; draft?: EmailDraft }> {
  const res = await apiFetch(`${base()}/drafts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ to: input.to, subject: input.subject || "", body: input.body }),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function sendDraftPreflight(draftId: string): Promise<{ ok: boolean; error?: string; preflight_id?: string; requires_approval?: boolean }> {
  const res = await apiFetch(`${base()}/drafts/${encodeURIComponent(draftId)}/send-preflight`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}
