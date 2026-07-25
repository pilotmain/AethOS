import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeConvergenceCognitionState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  convergence_cognition?: {
    summary?: string;
    converging?: boolean;
    trajectories?: { summary?: string; trajectory_improving?: boolean };
    replay_convergence?: { summary?: string; continuity_evolution?: string };
    dependency_convergence?: { summary?: string };
    topology_convergence?: { summary?: string };
  };
  infrastructure_intuition?: { summary?: string; intuition_active?: boolean };
  temporal_confidence?: { summary?: string; temporally_qualified?: boolean; confidence_evolution?: { summary?: string } };
  kubernetes_convergence?: { summary?: string; converged?: boolean };
  replay_continuity?: { summary?: string; continuity_stable?: boolean };
  operational_memory?: { summary?: string; memory_active?: boolean };
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

export const fetchRuntimeConvergenceCognitionState = () =>
  mcFetch<RuntimeConvergenceCognitionState>("/api/v1/runtime-convergence-cognition/state");

export const fetchInfrastructureIntuition = () =>
  mcFetch<RuntimeConvergenceCognitionState["infrastructure_intuition"]>(
    "/api/v1/runtime-convergence-cognition/infrastructure-intuition",
  );

export const fetchTemporalConfidence = () =>
  mcFetch<RuntimeConvergenceCognitionState["temporal_confidence"]>(
    "/api/v1/runtime-convergence-cognition/temporal-confidence",
  );

export const fetchKubernetesConvergence = () =>
  mcFetch<RuntimeConvergenceCognitionState["kubernetes_convergence"]>(
    "/api/v1/runtime-convergence-cognition/kubernetes",
  );

export const fetchReplayContinuityIntelligence = () =>
  mcFetch<RuntimeConvergenceCognitionState["replay_continuity"]>(
    "/api/v1/runtime-convergence-cognition/replay-continuity",
  );

export const fetchOperationalMemory = () =>
  mcFetch<RuntimeConvergenceCognitionState["operational_memory"]>(
    "/api/v1/runtime-convergence-cognition/operational-memory",
  );

export const fetchRealityHarnessV42 = () =>
  mcFetch<RuntimeConvergenceCognitionState["harness"]>("/api/v1/reality-harness-v42/scenarios");
