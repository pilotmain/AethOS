/** Connections catalog API — registry + live connection state. */

import { mcFetch } from "@/lib/missionControl/fetch";
import type { ProviderCapability, ProviderCatalogEntry } from "@/lib/missionControl/providerCatalog";
import type { ApiCredentialUi } from "@/lib/missionControl/providerCredentialConfig";

export type CapabilitySummary = {
  readonly: number;
  mutation: number;
  unsupported: number;
};

export type CatalogProviderEntry = ProviderCatalogEntry & {
  category?: string;
  credential_ui?: ApiCredentialUi;
  connection_state?: string;
  preferred_method?: string;
  connected_methods?: Record<string, string>;
  credentials_count?: number;
  capability_summary?: CapabilitySummary;
  engineering_view?: string;
};

export type CatalogChannelEntry = {
  name: string;
  label: string;
  category?: string;
  kind?: string;
  configured?: boolean;
  connection_state?: string;
  host_requirement?: string;
  capabilities?: {
    inbound?: boolean;
    outbound?: boolean;
    approval_transport?: boolean;
    evidence_transport?: boolean;
  };
  enabled?: boolean;
  token_configured?: boolean;
  token_source?: string;
  transport_health?: string;
  webhook_path?: string;
  webhook?: {
    configured?: boolean;
    url?: string;
    pending_update_count?: number;
    last_error_message?: string | null;
  };
  readonly_execution_via_mc?: boolean;
  approvals_via_mc?: boolean;
  last_received_at?: number | null;
  last_sent_at?: number | null;
  active_chats_count?: number;
  last_send_ok?: boolean | null;
  delivery_success_rate?: number | null;
  active_sessions?: Array<{
    session_id?: string;
    chat_id_masked?: string;
    last_operation?: string;
  }>;
};

export type ConnectionsCatalogResponse = {
  connected_providers: CatalogProviderEntry[];
  available_providers: CatalogProviderEntry[];
  backend_ready_providers?: CatalogProviderEntry[];
  connected_channels: CatalogChannelEntry[];
  available_channels: CatalogChannelEntry[];
};

export async function fetchConnectionsCatalog(): Promise<ConnectionsCatalogResponse> {
  return mcFetch("/api/v1/catalog/connections");
}

/** Providers that accept API keys — same filter Mission Control → Connections uses. */
export function credentialManageableProviders(catalog: ConnectionsCatalogResponse): CatalogProviderEntry[] {
  const seen = new Set<string>();
  const merged = [
    ...catalog.connected_providers,
    ...(catalog.backend_ready_providers ?? []),
    ...catalog.available_providers,
  ];
  const out: CatalogProviderEntry[] = [];
  for (const entry of merged) {
    if (seen.has(entry.name)) continue;
    seen.add(entry.name);
    if (!entry.credential_ui?.manage_credentials) continue;
    out.push(entry);
  }
  return out.sort((a, b) => a.label.localeCompare(b.label));
}

export function providerHasStoredCredentials(entry: CatalogProviderEntry): boolean {
  return (entry.credentials_count ?? 0) > 0 || entry.connection_state === "connected";
}

export function connectionStateLabel(state: string | undefined): string {
  switch (state) {
    case "connected":
      return "Connected";
    case "partially_configured":
      return "Partially configured";
    case "setup_needed":
      return "Setup needed";
    case "unavailable_on_this_host":
      return "Needs host dependency";
    case "ready":
      return "Ready to connect";
    case "coming_soon":
      return "Coming soon";
    case "backend_ready":
      return "Backend ready";
    case "disconnected":
      return "Disconnected";
    default:
      return state?.replace(/_/g, " ") ?? "Unknown";
  }
}

export function categoryLabel(category: string | undefined): string {
  if (!category) return "Provider";
  return category.charAt(0).toUpperCase() + category.slice(1);
}

export function transportHealthLabel(health: string | undefined): string {
  switch (health) {
    case "ok":
      return "Transport OK";
    case "disabled":
      return "Disabled";
    case "token_missing":
      return "Token missing";
    case "gateway_disabled":
      return "Gateway disabled — set CHANNEL_GATEWAY_ENABLED=true on Railway";
    default:
      return health?.replace(/_/g, " ") ?? "Unknown";
  }
}

export function formatActivityTimestamp(unixSeconds: number | null | undefined): string {
  if (unixSeconds == null || !Number.isFinite(unixSeconds)) {
    return "Never";
  }
  return new Date(unixSeconds * 1000).toLocaleString();
}
