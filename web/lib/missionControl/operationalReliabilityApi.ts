import { mcFetch } from "@/lib/missionControl/fetch";

export type ReliabilityScenario = {
  id: string;
  name: string;
  verification: string[];
  status: string;
  coverage_pct: number;
  harness_version: string;
};

export type OperationalReliabilityState = {
  ok: boolean;
  phase: string;
  harness_version?: string;
  production_reliable?: boolean;
  summary: string;
  capabilities?: Record<string, string>;
  continuous_verification?: { summary: string; sustained?: boolean; verification_coverage_pct?: number };
  recovery_orchestration?: { summary: string; coordinated?: boolean };
  drift_intelligence?: { summary: string; drift_bounded?: boolean };
  predictive_operations?: { summary: string };
  production_confidence?: { narrative: string; trust?: { qualification_tier?: string; infrastructure_trust_score?: number } };
  harness?: {
    harness_version: string;
    scenario_count: number;
    verified_count: number;
    average_coverage_pct: number;
    scenarios: ReliabilityScenario[];
  };
};

export const fetchOperationalReliabilityState = () =>
  mcFetch<OperationalReliabilityState>("/api/v1/operational-reliability/state");

export const fetchContinuousVerification = () =>
  mcFetch<{ summary: string; sustained?: boolean }>("/api/v1/operational-reliability/continuous-verification");

export const fetchRecoveryOrchestration = () =>
  mcFetch<{ summary: string; coordinated?: boolean }>("/api/v1/operational-reliability/recovery-orchestration");

export const fetchDriftIntelligence = () =>
  mcFetch<{ summary: string; drift_bounded?: boolean }>("/api/v1/operational-reliability/drift-intelligence");

export const fetchPredictiveOperations = () =>
  mcFetch<{ summary: string; trajectory?: { trajectory?: string } }>("/api/v1/operational-reliability/predictive-operations");

export const fetchProductionConfidence = () =>
  mcFetch<{ narrative: string; trust?: { qualification_tier?: string } }>("/api/v1/operational-reliability/production-confidence");

export const fetchReliabilityHarness = () =>
  mcFetch<OperationalReliabilityState["harness"]>("/api/v1/operational-reliability/harness/scenarios");
