import { mcFetch } from "@/lib/missionControl/fetch";

export type OperationalResilienceState = {
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
  runtime_fragility?: { summary?: string; fragility_elevated?: boolean };
  sustained_trust_evolution?: { summary?: string; trust_evolving?: boolean };
  kubernetes_durability?: { summary?: string; durable?: boolean };
  replay_resilience?: { summary?: string; resilient?: boolean };
  long_tail_resilience?: { summary?: string; memory_active?: boolean };
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

export const fetchOperationalResilienceState = () =>
  mcFetch<OperationalResilienceState>("/api/v1/operational-resilience/state");

export const fetchRuntimeFragility = () =>
  mcFetch<OperationalResilienceState["runtime_fragility"]>("/api/v1/operational-resilience/runtime-fragility");

export const fetchSustainedTrustEvolution = () =>
  mcFetch<OperationalResilienceState["sustained_trust_evolution"]>("/api/v1/operational-resilience/sustained-trust");

export const fetchKubernetesRuntimeDurability = () =>
  mcFetch<OperationalResilienceState["kubernetes_durability"]>("/api/v1/operational-resilience/kubernetes-durability");

export const fetchReplayResilienceCognition = () =>
  mcFetch<OperationalResilienceState["replay_resilience"]>("/api/v1/operational-resilience/replay-resilience");

export const fetchOperationalResilienceLongTail = () =>
  mcFetch<{ summary?: string; long_tail_stable?: boolean }>("/api/v1/operational-resilience/long-tail-stability");

export const fetchOperationalRecoveryDurability = () =>
  mcFetch<{ summary?: string; durable?: boolean }>("/api/v1/operational-resilience/recovery-durability");

export const fetchOperationalResilienceMemory = () =>
  mcFetch<OperationalResilienceState["long_tail_resilience"]>("/api/v1/operational-resilience/resilience-memory");

export const fetchRealityHarnessV43Operational = () =>
  mcFetch<OperationalResilienceState["harness"]>("/api/v1/reality-harness-v43/scenarios");
