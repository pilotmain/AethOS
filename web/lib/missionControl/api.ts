/** Mission Control API — isolated from chat; failures stay in MC panels only. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeStatus = {
  status: string;
  chat_ready: boolean;
  api_port: number;
  provider: {
    real_llm: boolean;
    active_provider: string;
    model: string;
    ready: boolean;
  };
  capabilities: {
    browser_automation: boolean;
    host_executor: boolean;
    vercel_cli_on_path: boolean;
  };
};

export type { ActionsGrouped, RuntimeActionRecord } from "@/lib/missionControl/actions";
export type { JobsGrouped, TrackedJobRecord, TrackedJobsResponse } from "@/lib/missionControl/trackedJobs";

export type SettingsSummary = {
  response_mode: string;
  use_real_llm: boolean;
  active_provider: string;
  model: string;
  provider_ready: boolean;
  browser_automation_enabled: boolean;
  host_executor_enabled: boolean;
};

export type ProviderReadinessResponse = import("@/lib/missionControl/providerReadiness").ProviderReadiness;

export const fetchRuntimeStatus = () => mcFetch<RuntimeStatus>("/api/v1/runtime/status");
export { fetchActionsGrouped } from "@/lib/missionControl/actions";
export { fetchTrackedJobs } from "@/lib/missionControl/trackedJobs";
export const fetchMcSettings = () => mcFetch<SettingsSummary>("/api/v1/settings");
export { fetchBrowserStatus } from "@/lib/missionControl/browserSessions";
export const fetchProviderReadiness = () =>
  mcFetch<ProviderReadinessResponse>("/api/v1/settings/provider");
