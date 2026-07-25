import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeTruthState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  reconciliation?: {
    summary?: string;
    narrative?: string;
    reconciled?: boolean;
    topology_alignment?: { summary?: string; aligned?: boolean };
    replay_alignment?: { summary?: string; aligned?: boolean };
  };
  operational_patience?: { summary?: string; patience_maintained?: boolean };
  runtime_decay?: { summary?: string; decay_bounded?: boolean };
  verification_windows?: {
    summary?: string;
    window_qualified?: boolean;
    verification_windows?: { window_satisfied?: boolean; summary?: string };
  };
  recovery_truth?: { summary?: string; converged?: boolean };
  harness?: {
    harness_version: string;
    scenario_count: number;
    verified_count: number;
    average_coverage_pct: number;
    scenarios?: { id: string; name: string; status: string; coverage_pct: number }[];
  };
  strategic_position?: Record<string, string>;
  principles?: Record<string, string>;
};

export const fetchRuntimeReconciliationState = () =>
  mcFetch<RuntimeTruthState>("/api/v1/runtime-reconciliation/state");

export const fetchOperationalPatience = () =>
  mcFetch<RuntimeTruthState["operational_patience"]>("/api/v1/runtime-reconciliation/patience");

export const fetchRuntimeDecay = () =>
  mcFetch<RuntimeTruthState["runtime_decay"]>("/api/v1/runtime-reconciliation/decay");

export const fetchVerificationWindows = () =>
  mcFetch<RuntimeTruthState["verification_windows"]>("/api/v1/runtime-reconciliation/verification-windows");

export const fetchRecoveryTruth = () =>
  mcFetch<RuntimeTruthState["recovery_truth"]>("/api/v1/runtime-reconciliation/recovery-truth");

export const fetchRealityHarnessV41 = () =>
  mcFetch<RuntimeTruthState["harness"]>("/api/v1/reality-harness-v41/scenarios");
