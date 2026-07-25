import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeFragilityIntelligenceState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  runtime_fragility?: {
    summary?: string;
    fragility_emerging?: boolean;
  };
  degradation_acceleration?: { summary?: string; acceleration_detected?: boolean };
  replay_erosion?: { summary?: string };
  topology_fragility?: { summary?: string; fragility_bounded?: boolean };
  operational_fatigue?: { summary?: string; fatigue_elevated?: boolean };
  predictive_stability?: { summary?: string; stability_projected?: boolean };
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

export const fetchRuntimeFragilityIntelligenceState = () =>
  mcFetch<RuntimeFragilityIntelligenceState>("/api/v1/runtime-fragility-intelligence/state");

export const fetchDegradationAcceleration = () =>
  mcFetch<RuntimeFragilityIntelligenceState["degradation_acceleration"]>(
    "/api/v1/runtime-fragility-intelligence/degradation-acceleration",
  );

export const fetchReplayErosionIntelligence = () =>
  mcFetch<RuntimeFragilityIntelligenceState["replay_erosion"]>(
    "/api/v1/runtime-fragility-intelligence/replay-erosion",
  );

export const fetchTopologyFragilityForecasting = () =>
  mcFetch<RuntimeFragilityIntelligenceState["topology_fragility"]>(
    "/api/v1/runtime-fragility-intelligence/topology-fragility",
  );

export const fetchOperationalFatigueCognition = () =>
  mcFetch<RuntimeFragilityIntelligenceState["operational_fatigue"]>(
    "/api/v1/runtime-fragility-intelligence/operational-fatigue",
  );

export const fetchPredictiveRuntimeStability = () =>
  mcFetch<RuntimeFragilityIntelligenceState["predictive_stability"]>(
    "/api/v1/runtime-fragility-intelligence/predictive-stability",
  );

export const fetchRecoveryFragility = () =>
  mcFetch<{ summary?: string; accelerating?: boolean }>(
    "/api/v1/runtime-fragility-intelligence/degradation-acceleration",
  );

export const fetchFragilityMemory = () =>
  mcFetch<{ ok: boolean; fragility_zones_tracked?: number }>(
    "/api/v1/runtime-fragility-intelligence/fragility-memory",
  );

export const fetchRealityHarnessV44Fragility = () =>
  mcFetch<RuntimeFragilityIntelligenceState["harness"]>("/api/v1/reality-harness-v44/scenarios");
