/** Provider catalog API — neutral provider list for Connections UI. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ProviderCapability = {
  operation: string;
  read_only: boolean;
  mutation: boolean;
  api_supported: boolean | string;
  browser_fallback: boolean | string;
  browser_required: boolean;
  requires_approval: boolean;
  enabled: boolean;
};

export type ProviderCatalogEntry = {
  name: string;
  label: string;
  connected: boolean;
  capabilities: Record<string, ProviderCapability>;
  mutations_enabled: boolean;
};

export type ProviderCatalogResponse = {
  providers: ProviderCatalogEntry[];
  count: number;
};

export async function fetchProviderCatalog(): Promise<ProviderCatalogResponse> {
  return mcFetch("/api/v1/providers");
}

export const PLANNED_PROVIDERS = [] as const;

export function readonlyCapabilityCount(entry: ProviderCatalogEntry): number {
  return Object.values(entry.capabilities).filter((c) => c.read_only && c.enabled).length;
}
