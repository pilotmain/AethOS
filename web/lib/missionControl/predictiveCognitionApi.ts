import { mcFetch } from "@/lib/missionControl/fetch";

export type PredictiveOperationalCognitionState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  predictive_cognition?: {
    summary?: string;
    predictively_stable?: boolean;
    replay_forecasting?: { summary?: string };
  };
  fragility_acceleration?: { summary?: string; acceleration_detected?: boolean };
  replay_erosion_forecasting?: { summary?: string };
  topology_stability_forecasting?: { summary?: string; topology_stable?: boolean };
  operational_fatigue?: { summary?: string; fatigue_elevated?: boolean };
  sustained_stability_forecasting?: { summary?: string; stability_projected?: boolean };
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

export const fetchPredictiveOperationalCognitionState = () =>
  mcFetch<PredictiveOperationalCognitionState>("/api/v1/predictive-operational-cognition/state");

export const fetchFragilityAcceleration = () =>
  mcFetch<PredictiveOperationalCognitionState["fragility_acceleration"]>(
    "/api/v1/predictive-operational-cognition/fragility-acceleration",
  );

export const fetchReplayForecasting = () =>
  mcFetch<PredictiveOperationalCognitionState["replay_erosion_forecasting"]>(
    "/api/v1/predictive-operational-cognition/replay-forecasting",
  );

export const fetchTopologyForecasting = () =>
  mcFetch<PredictiveOperationalCognitionState["topology_stability_forecasting"]>(
    "/api/v1/predictive-operational-cognition/topology-forecasting",
  );

export const fetchOperationalFatigue = () =>
  mcFetch<PredictiveOperationalCognitionState["operational_fatigue"]>(
    "/api/v1/predictive-operational-cognition/operational-fatigue",
  );

export const fetchStabilityProjection = () =>
  mcFetch<PredictiveOperationalCognitionState["sustained_stability_forecasting"]>(
    "/api/v1/predictive-operational-cognition/stability-projection",
  );

export const fetchRecoveryForecasting = () =>
  mcFetch<{ summary?: string; projection_stable?: boolean }>(
    "/api/v1/predictive-operational-cognition/recovery-forecasting",
  );

export const fetchPredictiveMemory = () =>
  mcFetch<{ ok: boolean; trajectory_history_count?: number }>(
    "/api/v1/predictive-operational-cognition/predictive-memory",
  );

export const fetchRealityHarnessV44 = () =>
  mcFetch<PredictiveOperationalCognitionState["harness"]>("/api/v1/reality-harness-v44/scenarios");
