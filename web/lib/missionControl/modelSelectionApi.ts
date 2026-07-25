/** Per-provider model selection API — choose which models a provider exposes. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ProviderModel = {
  model_id: string;
  label: string;
  enabled: boolean;
  custom: boolean;
};

export type ProviderModelSelection = {
  ok?: boolean;
  provider: string;
  label: string;
  configured: boolean;
  models: ProviderModel[];
  api_key_url?: string;
};

export const fetchProviderModelSelection = (provider: string) =>
  mcFetch<ProviderModelSelection>(`/api/v1/models/providers/${encodeURIComponent(provider)}`);

export const saveProviderModelSelection = (
  provider: string,
  enabledIds: string[],
  customIds: string[],
) =>
  mcFetch<ProviderModelSelection>(`/api/v1/models/providers/${encodeURIComponent(provider)}`, {
    method: "POST",
    body: JSON.stringify({ enabled_ids: enabledIds, custom_ids: customIds }),
  });
