import { mcFetch } from "@/lib/missionControl/fetch";

export type OperationalResilienceCognitionState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  operational_resilience?: {
    summary?: string;
    resilient?: boolean;
    trajectories?: { summary?: string };
  };
  infrastructure_fragility?: { summary?: string; fragility_elevated?: boolean };
  temporal_trust_evolution?: { summary?: string; trust_evolving?: boolean };
  kubernetes_resilience?: { summary?: string; resilient?: boolean };
  replay_resilience?: { summary?: string; resilient?: boolean };
  resilience_memory?: { summary?: string; memory_active?: boolean };
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

export const fetchOperationalResilienceCognitionState = () =>
  mcFetch<OperationalResilienceCognitionState>("/api/v1/operational-resilience-cognition/state");

export const fetchInfrastructureFragility = () =>
  mcFetch<OperationalResilienceCognitionState["infrastructure_fragility"]>(
    "/api/v1/operational-resilience-cognition/infrastructure-fragility",
  );

export const fetchTemporalTrustEvolution = () =>
  mcFetch<OperationalResilienceCognitionState["temporal_trust_evolution"]>(
    "/api/v1/operational-resilience-cognition/temporal-trust",
  );

export const fetchKubernetesResilience = () =>
  mcFetch<OperationalResilienceCognitionState["kubernetes_resilience"]>(
    "/api/v1/operational-resilience-cognition/kubernetes-resilience",
  );

export const fetchReplayResilience = () =>
  mcFetch<OperationalResilienceCognitionState["replay_resilience"]>(
    "/api/v1/operational-resilience-cognition/replay-resilience",
  );

export const fetchResilienceLongTailStability = () =>
  mcFetch<{ summary?: string; long_tail_stable?: boolean }>(
    "/api/v1/operational-resilience-cognition/long-tail-stability",
  );

export const fetchRecoveryDurability = () =>
  mcFetch<{ summary?: string; durable?: boolean }>(
    "/api/v1/operational-resilience-cognition/recovery-durability",
  );

export const fetchResilienceMemory = () =>
  mcFetch<OperationalResilienceCognitionState["resilience_memory"]>(
    "/api/v1/operational-resilience-cognition/resilience-memory",
  );

export const fetchRealityHarnessV43 = () =>
  mcFetch<OperationalResilienceCognitionState["harness"]>("/api/v1/reality-harness-v43/scenarios");
