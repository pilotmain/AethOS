import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeTruthConvergenceState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  runtime_truth?: {
    summary?: string;
    narrative?: string;
    converged?: boolean;
    replay_truth?: { summary?: string; replay_converged?: boolean };
    topology_truth?: { summary?: string; topology_converged?: boolean };
    alignment?: { aligned_count?: number; total_layers?: number };
  };
  stability_windows?: { summary?: string; window_qualified?: boolean };
  recovery_convergence?: { summary?: string; continuously_reconciled?: boolean };
  long_tail_decay?: { summary?: string; decay_bounded?: boolean };
  adaptive_verification?: { summary?: string; adaptively_qualified?: boolean };
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

export const fetchRuntimeTruthConvergenceState = () =>
  mcFetch<RuntimeTruthConvergenceState>("/api/v1/runtime-truth-convergence/state");

export const fetchStabilityWindows = () =>
  mcFetch<RuntimeTruthConvergenceState["stability_windows"]>("/api/v1/runtime-truth-convergence/stability-windows");

export const fetchRecoveryConvergence = () =>
  mcFetch<RuntimeTruthConvergenceState["recovery_convergence"]>("/api/v1/runtime-truth-convergence/recovery");

export const fetchAdaptiveVerification = () =>
  mcFetch<RuntimeTruthConvergenceState["adaptive_verification"]>("/api/v1/runtime-truth-convergence/adaptive-verification");

export const fetchLongTailDecay = () =>
  mcFetch<RuntimeTruthConvergenceState["long_tail_decay"]>("/api/v1/runtime-truth-convergence/long-tail-decay");

export const fetchRealityHarnessV41 = () =>
  mcFetch<RuntimeTruthConvergenceState["harness"]>("/api/v1/reality-harness-v41/scenarios");
