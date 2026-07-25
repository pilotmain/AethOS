/** Production reliability API — Phase 11.1 Mission Control client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type Tier1Provider = {
  provider: string;
  capabilities: string[];
  maturity: string;
  verification_coverage_pct: number;
  hardening_status: string;
};

export type ProductionReliabilityState = {
  ok: boolean;
  harness_version?: string;
  tier1_providers?: Tier1Provider[];
  tier1_capabilities?: Record<string, unknown>[];
  matrix_summary?: Record<string, unknown>;
  harness?: Record<string, unknown>;
};

export const fetchProductionReliabilityState = () =>
  mcFetch<ProductionReliabilityState>("/api/v1/production-reliability/state");

export const fetchTier1Providers = () =>
  mcFetch<{ ok: boolean; providers: Tier1Provider[]; harness_version: string }>(
    "/api/v1/production-reliability/providers",
  );

export const fetchMutationReconciliation = (jobId: string) =>
  mcFetch<{ ok: boolean; reconciled?: boolean; summary?: string; verification?: Record<string, unknown> }>(
    `/api/v1/production-reliability/reconciliation/${jobId}`,
  );

export const fetchRecoveryRuntime = (jobId: string) =>
  mcFetch<{ ok: boolean; narrative?: string; resolved_claim_allowed?: boolean; confidence?: Record<string, unknown> }>(
    `/api/v1/production-reliability/recovery/${jobId}`,
  );
