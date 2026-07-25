/** Telegram channel settings API. */

import { apiBase } from "@/lib/api";
import { mcFetch } from "@/lib/missionControl/fetch";
import {
  formatConnectionSaveError,
  parseConnectionErrorPayload,
} from "@/lib/missionControl/connectionErrors";
import type { CredentialRecord, CredentialVaultDiagnostics } from "@/lib/missionControl/connectionsApi";

export type TelegramWebhookInfo = {
  configured?: boolean;
  url?: string;
  pending_update_count?: number;
  last_error_message?: string | null;
  error?: string;
};

export type TelegramSessionEntry = {
  session_id?: string;
  chat_id_masked?: string;
  user_id_masked?: string;
  last_received_at?: number;
  last_sent_at?: number;
  last_message_preview?: string;
  last_operation?: string;
  session_state?: string;
  pending_approval_job_id?: string | null;
};

export type TelegramTypingDiagnostics = {
  typing_enabled?: boolean;
  progress_messages_enabled?: boolean;
  typing_interval_seconds?: number;
  progress_after_seconds?: number;
  last_typing_sent_at?: number | null;
  last_typing_error?: string | null;
  typing_send_count?: number;
};

export type TelegramChannelStatus = {
  name: string;
  label: string;
  enabled?: boolean;
  channel_gateway_enabled?: boolean;
  token_configured?: boolean;
  token_source?: string;
  transport_health?: string;
  webhook_path?: string;
  expected_webhook_url?: string;
  webhook_mismatch?: boolean;
  webhook?: TelegramWebhookInfo;
  last_received_at?: number | null;
  last_sent_at?: number | null;
  active_chats_count?: number;
  last_send_ok?: boolean | null;
  last_send_error?: string | null;
  delivery_success_rate?: number | null;
  credentials?: CredentialRecord[];
  connected_methods?: Record<string, string>;
  credential_vault?: CredentialVaultDiagnostics;
  active_sessions?: TelegramSessionEntry[];
  typing?: TelegramTypingDiagnostics;
  telegram_api_status?: string;
};

export type TelegramConnection = {
  provider: string;
  preferred_method: string;
  connected_methods: Record<string, string>;
  credentials: CredentialRecord[];
  credential_vault?: CredentialVaultDiagnostics;
};

const TELEGRAM_CREDENTIALS_PATH = "/api/v1/channels/telegram/credentials";

export function telegramCredentialsSaveUrl(): string {
  return `${apiBase()}${TELEGRAM_CREDENTIALS_PATH}`;
}

export function telegramWebhookUrl(): string {
  return `${apiBase()}/api/v1/channels/telegram/webhook`;
}

export async function fetchTelegramStatus(): Promise<TelegramChannelStatus> {
  return mcFetch("/api/v1/channels/telegram/status");
}

export async function registerTelegramWebhookLocal(): Promise<{
  ok: boolean;
  webhook_url?: string;
  telegram_webhook_status?: string;
  detail?: string;
  error?: string;
}> {
  return mcFetch("/api/v1/channels/telegram/webhook/register", { method: "POST", body: "{}" });
}

/** @deprecated use registerTelegramWebhookLocal */
export const registerTelegramWebhook = registerTelegramWebhookLocal;

export async function registerTelegramProductionWebhook(): Promise<{
  ok: boolean;
  webhook_url?: string;
  registered_webhook_url?: string;
  verified?: boolean;
  detail?: string;
  error?: string;
}> {
  return mcFetch("/api/v1/channels/telegram/webhook/register/production", { method: "POST", body: "{}" });
}

export async function fetchTelegramConnection(): Promise<TelegramConnection> {
  return mcFetch("/api/v1/channels/telegram/connection");
}

export async function fetchTelegramSessions(): Promise<{ sessions: TelegramSessionEntry[]; count: number }> {
  return mcFetch("/api/v1/channels/telegram/sessions");
}

export type StoreTelegramTokenResult = {
  ok: boolean;
  credential?: CredentialRecord;
  test?: { ok?: boolean; detail?: string; bot_username?: string };
  code?: string;
  detail?: string;
};

export async function storeTelegramBotToken(body: {
  label: string;
  token: string;
}): Promise<StoreTelegramTokenResult> {
  const requestUrl = telegramCredentialsSaveUrl();
  try {
    const res = await fetch(requestUrl, {
      method: "POST",
      cache: "no-store",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ label: body.label, token: body.token }),
    });
    const text = await res.text();
    let data: StoreTelegramTokenResult = { ok: false };
    try {
      data = JSON.parse(text) as StoreTelegramTokenResult;
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
    const formatted = formatConnectionSaveError(err, { requestUrl });
    throw new Error(formatted.message);
  }
}

export async function testTelegramCredential(
  credentialId: string,
): Promise<{ test: { ok?: boolean; detail?: string; bot_username?: string } }> {
  return mcFetch(
    `/api/v1/channels/telegram/credentials/${encodeURIComponent(credentialId)}/test`,
    { method: "POST", body: "{}" },
  );
}

export async function revokeTelegramCredential(credentialId: string): Promise<{ revoked: boolean }> {
  return mcFetch(
    `/api/v1/channels/telegram/credentials/${encodeURIComponent(credentialId)}/revoke`,
    { method: "POST", body: "{}" },
  );
}

export async function sendTelegramTestMessage(body: {
  chat_id: string;
  message?: string;
}): Promise<{ ok: boolean; sent?: boolean; detail?: string; code?: string }> {
  return mcFetch("/api/v1/channels/telegram/test-send", {
    method: "POST",
    body: JSON.stringify({
      chat_id: body.chat_id,
      message: body.message ?? "AethOS Telegram connection test.",
    }),
  });
}

export async function fetchTelegramPreferences(): Promise<{
  default_mode?: string;
  session_modes?: Record<string, string>;
}> {
  return mcFetch("/api/v1/channels/telegram/preferences");
}

export async function setTelegramNotifyMode(body: {
  mode: string;
  session_id?: string;
}): Promise<{ ok: boolean; default_mode?: string }> {
  return mcFetch("/api/v1/channels/telegram/preferences", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type PairingPendingEntry = {
  channel: string;
  external_user_id: string;
  code: string;
  preview?: string;
  created_at?: string;
};

export type PairingAllowedEntry = {
  channel: string;
  external_user_id: string;
  paired_at?: string;
};

export type PairingStatus = {
  ok: boolean;
  channel_gateway_enabled?: boolean;
  channel_dm_policy?: string;
  pending_count?: number;
  allowed_count?: number;
  pending: PairingPendingEntry[];
  allowed: PairingAllowedEntry[];
};

export async function fetchPairingStatus(): Promise<PairingStatus> {
  return mcFetch("/api/v1/channels/pairing/status");
}

export async function approvePairing(body: {
  channel: string;
  code: string;
}): Promise<{ ok: boolean; status?: string; channel?: string; external_user_id?: string; error?: string }> {
  return mcFetch("/api/v1/channels/pairing/approve", {
    method: "POST",
    body: JSON.stringify({ channel: body.channel, code: body.code }),
  });
}

export async function revokePairing(body: {
  channel: string;
  external_user_id: string;
}): Promise<{ ok: boolean; revoked?: number; channel?: string; external_user_id?: string }> {
  return mcFetch("/api/v1/channels/pairing/revoke", {
    method: "POST",
    body: JSON.stringify({ channel: body.channel, external_user_id: body.external_user_id }),
  });
}

// --- Generic per-channel credential flow (Slack, Discord, WhatsApp, …) ---

export type ChannelCredentialFieldSchema = {
  id: string;
  label: string;
  secret: boolean;
  required: boolean;
  placeholder?: string;
  help?: string;
};

export type ChannelCredentialSchema = {
  channel_id: string;
  label: string;
  primary_field: string;
  fields: ChannelCredentialFieldSchema[];
  webhook_path?: string | null;
  default_label?: string;
  description?: string;
};

export type ChannelConnection = {
  ok: boolean;
  channel: string;
  supports_credentials: boolean;
  schema?: ChannelCredentialSchema | null;
  configured: boolean;
  credentials: CredentialRecord[];
  webhook_path?: string | null;
  credential_vault?: CredentialVaultDiagnostics;
};

export async function fetchChannelConnection(channelId: string): Promise<ChannelConnection> {
  return mcFetch(`/api/v1/channels/${encodeURIComponent(channelId)}/connection`);
}

export async function storeChannelCredentials(
  channelId: string,
  body: { label: string; fields: Record<string, string> },
): Promise<{ ok: boolean; credential?: CredentialRecord; test?: { ok?: boolean; detail?: string } }> {
  return mcFetch(`/api/v1/channels/${encodeURIComponent(channelId)}/credentials`, {
    method: "POST",
    body: JSON.stringify({ label: body.label, fields: body.fields }),
  });
}

export async function testChannelCredential(
  channelId: string,
  credentialId: string,
): Promise<{ ok: boolean; test?: { ok?: boolean; detail?: string } }> {
  return mcFetch(
    `/api/v1/channels/${encodeURIComponent(channelId)}/credentials/${encodeURIComponent(credentialId)}/test`,
    { method: "POST", body: "{}" },
  );
}

export async function revokeChannelCredential(
  channelId: string,
  credentialId: string,
): Promise<{ ok: boolean; revoked?: boolean }> {
  return mcFetch(
    `/api/v1/channels/${encodeURIComponent(channelId)}/credentials/${encodeURIComponent(credentialId)}/revoke`,
    { method: "POST", body: "{}" },
  );
}

export function channelWebhookUrl(webhookPath: string | null | undefined): string {
  if (!webhookPath) return "";
  return `${apiBase()}${webhookPath}`;
}

export function tokenSourceLabel(source: string | undefined): string {
  switch (source) {
    case "vault":
      return "Credential vault";
    case "env":
      return "Environment variable";
    default:
      return "Not configured";
  }
}
