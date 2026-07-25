/** Production infrastructure — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export const fetchProductionTopology = () => mcFetch<Record<string, unknown>>("/api/v1/production/topology");

export const fetchProductionCluster = () => mcFetch<Record<string, unknown>>("/api/v1/production/cluster");

export const fetchProductionEdge = () => mcFetch<Record<string, unknown>>("/api/v1/production/edge");

export const fetchOrgsCurrent = () => mcFetch<Record<string, unknown>>("/api/v1/orgs/current");

export const fetchObservabilityDashboard = () => mcFetch<Record<string, unknown>>("/api/v1/observability/dashboard");

export const fetchObservabilityMetering = () => mcFetch<Record<string, unknown>>("/api/v1/observability/metering");

export const fetchObservabilitySlo = () => mcFetch<Record<string, unknown>>("/api/v1/observability/slo");

export const fetchRouteTrace = (sessionId = "default") =>
  mcFetch<Record<string, unknown>>(`/api/v1/observability/route-trace/${encodeURIComponent(sessionId)}`);

export const fetchJobTrace = (jobId: string) =>
  mcFetch<Record<string, unknown>>(`/api/v1/observability/job-trace/${encodeURIComponent(jobId)}`);

export const fetchPlugins = () => mcFetch<{ ok: boolean; plugins?: unknown[] }>("/api/v1/plugins");

export const fetchUpgradeStatus = () => mcFetch<Record<string, unknown>>("/api/v1/upgrade/status");

export const runUpgrade = () => mcFetch<Record<string, unknown>>("/api/v1/upgrade/run", { method: "POST" });

export const rollbackUpgrade = () => mcFetch<Record<string, unknown>>("/api/v1/upgrade/rollback", { method: "POST" });

export const fetchConfigMigration = () => mcFetch<Record<string, unknown>>("/api/v1/upgrade/config-migration");

export const checkRbac = (action: string, userId = "default") =>
  mcFetch<Record<string, unknown>>("/api/v1/orgs/rbac/check", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, action }),
  });
