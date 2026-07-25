import { mcFetch } from "@/lib/missionControl/fetch";

export type LongTailForecastingState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  long_tail_forecasting?: {
    summary?: string;
    forecastable?: boolean;
    replay_longevity?: { summary?: string };
  };
  operational_survivability?: { summary?: string; survivable?: boolean };
  replay_longevity_forecasting?: { summary?: string; continuity_durable?: boolean };
  topology_sustainability?: { summary?: string; sustainable?: boolean };
  resilience_exhaustion?: { summary?: string; exhaustion_emerging?: boolean };
  autonomous_stability?: { summary?: string; stability_enduring?: boolean };
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

export const fetchLongTailForecastingState = () =>
  mcFetch<LongTailForecastingState>("/api/v1/long-tail-operational-forecasting/state");

export const fetchOperationalSurvivability = () =>
  mcFetch<LongTailForecastingState["operational_survivability"]>(
    "/api/v1/long-tail-operational-forecasting/operational-survivability",
  );

export const fetchReplayLongevity = () =>
  mcFetch<LongTailForecastingState["replay_longevity_forecasting"]>(
    "/api/v1/long-tail-operational-forecasting/replay-longevity",
  );

export const fetchTopologySustainability = () =>
  mcFetch<LongTailForecastingState["topology_sustainability"]>(
    "/api/v1/long-tail-operational-forecasting/topology-sustainability",
  );

export const fetchResilienceExhaustion = () =>
  mcFetch<LongTailForecastingState["resilience_exhaustion"]>(
    "/api/v1/long-tail-operational-forecasting/resilience-exhaustion",
  );

export const fetchAutonomousStability = () =>
  mcFetch<LongTailForecastingState["autonomous_stability"]>(
    "/api/v1/long-tail-operational-forecasting/autonomous-stability",
  );

export const fetchForecastingMemory = () =>
  mcFetch<{ ok: boolean; forecast_history_count?: number }>(
    "/api/v1/long-tail-operational-forecasting/forecasting-memory",
  );

export const fetchRealityHarnessV45 = () =>
  mcFetch<LongTailForecastingState["harness"]>("/api/v1/reality-harness-v45/scenarios");
