/** Operational truth API — Phase 11.0 Mission Control client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CapabilityTruthRow = {
  id: string;
  name: string;
  category: string;
  provider?: string | null;
  claimed: boolean;
  real: string;
  verified: string;
  verification_coverage_pct: number;
  prod_ready: boolean;
  maturity: string;
  maturity_label: string;
  honest_summary: string;
};

export type OperationalTruthState = {
  ok: boolean;
  truth_state?: string;
  truth_degraded?: boolean;
  readiness_tier?: string;
  readiness_score?: number;
  verification_coverage_pct?: number;
  overclaim_risk?: boolean;
  summary?: string;
};

export type OperationalTruthFull = {
  ok: boolean;
  truth_state?: string;
  truth_degraded?: boolean;
  capability_matrix?: CapabilityTruthRow[];
  matrix_summary?: Record<string, unknown>;
  readiness?: Record<string, unknown>;
  execution_integrity?: Record<string, unknown>;
  operational_honesty?: Record<string, unknown>;
  capability_audit?: { audit_categories?: { category: string; status: string; coverage_pct: number; summary: string }[] };
  summary?: string;
};

export type RealityScenario = {
  id: string;
  name: string;
  provider?: string | null;
  status: string;
  coverage_pct: number;
};

export const fetchOperationalTruthState = () =>
  mcFetch<OperationalTruthState>("/api/v1/operational-truth/state");

export const fetchOperationalTruthFull = () =>
  mcFetch<OperationalTruthFull>("/api/v1/operational-truth/full");

export const fetchCapabilityMatrix = () =>
  mcFetch<{ ok: boolean; matrix: CapabilityTruthRow[]; summary: Record<string, unknown> }>(
    "/api/v1/operational-truth/capability-matrix",
  );

export const fetchProviderReadiness = () =>
  mcFetch<{ ok: boolean; providers: Record<string, unknown>[]; readiness: Record<string, unknown> }>(
    "/api/v1/operational-truth/providers",
  );

export const fetchCapabilityAudit = () =>
  mcFetch<{ ok: boolean; audit_categories: { category: string; status: string; coverage_pct: number; summary: string }[] }>(
    "/api/v1/operational-truth/audit",
  );

export const fetchConfidenceIntegrity = () =>
  mcFetch<{ ok: boolean; integrity: string; bounded_confidence?: number; summary?: string; penalties?: string[] }>(
    "/api/v1/operational-truth/confidence-integrity",
  );

export const fetchRealityHarnessState = () =>
  mcFetch<{ ok: boolean; scenarios: RealityScenario[]; average_coverage_pct?: number; summary?: string }>(
    "/api/v1/reality-harness/state",
  );

export const runRealityHarnessCycle = (windowHours = 48) =>
  mcFetch<{ ok: boolean; summary?: string }>("/api/v1/reality-harness/cycle", {
    method: "POST",
    body: JSON.stringify({ window_hours: windowHours, source: "mission_control" }),
  });
