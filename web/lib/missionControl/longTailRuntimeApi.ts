import { mcFetch } from "@/lib/missionControl/fetch";

export type LongTailRuntimeCognitionState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  long_tail_runtime_cognition?: {
    summary?: string;
    cognition_qualified?: boolean;
  };
  runtime_survivability_intelligence?: { summary?: string; survivable?: boolean };
  operational_endurance?: { summary?: string; enduring?: boolean };
  replay_continuity_survivability?: { summary?: string; continuity_sustainable?: boolean };
  topology_endurance_forecasting?: { summary?: string; enduring?: boolean };
  resilience_exhaustion_intelligence?: { summary?: string; exhaustion_emerging?: boolean };
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

export const fetchLongTailRuntimeCognitionState = () =>
  mcFetch<LongTailRuntimeCognitionState>("/api/v1/long-tail-runtime-cognition/state");

export const fetchRuntimeSurvivability = () =>
  mcFetch<LongTailRuntimeCognitionState["runtime_survivability_intelligence"]>(
    "/api/v1/long-tail-runtime-cognition/runtime-survivability",
  );

export const fetchOperationalEndurance = () =>
  mcFetch<LongTailRuntimeCognitionState["operational_endurance"]>(
    "/api/v1/long-tail-runtime-cognition/operational-endurance",
  );

export const fetchReplayContinuity = () =>
  mcFetch<LongTailRuntimeCognitionState["replay_continuity_survivability"]>(
    "/api/v1/long-tail-runtime-cognition/replay-continuity",
  );

export const fetchTopologyEndurance = () =>
  mcFetch<LongTailRuntimeCognitionState["topology_endurance_forecasting"]>(
    "/api/v1/long-tail-runtime-cognition/topology-endurance",
  );

export const fetchResilienceExhaustionIntelligence = () =>
  mcFetch<LongTailRuntimeCognitionState["resilience_exhaustion_intelligence"]>(
    "/api/v1/long-tail-runtime-cognition/resilience-exhaustion",
  );

export const fetchCognitionMemory = () =>
  mcFetch<{ ok: boolean; fatigue_history_count?: number }>(
    "/api/v1/long-tail-runtime-cognition/cognition-memory",
  );

export const fetchRealityHarnessV45Runtime = () =>
  mcFetch<LongTailRuntimeCognitionState["harness"]>("/api/v1/reality-harness-v45/scenarios");
