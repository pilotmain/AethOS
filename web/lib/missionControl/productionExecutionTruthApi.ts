import { mcFetch } from "@/lib/missionControl/fetch";

export type ProductionExecutionTruthState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  qualification_tier?: string;
  summary?: string;
  narrative?: string;
  execution_truth?: {
    convergence?: { summary?: string; narrative?: string };
    deployment_truth?: { deployment_truth_score?: number; summary?: string };
    operational_decay?: { decay_bounded?: boolean; current_confidence?: number };
  };
  provider_truth?: {
    providers?: Record<string, { summary?: string }>;
    topology_recovery?: { summary?: string; topology_converged?: boolean };
  };
  rollback_integrity?: { summary?: string; confidence?: { rollback_confidence?: number } };
  runtime_stabilization?: {
    summary?: string;
    sustained_health?: { sustained_health_qualified?: boolean; summary?: string };
    patience?: { premature_healthy_blocked?: boolean };
  };
  infrastructure_truth?: {
    summary?: string;
    score?: { infrastructure_truth_score?: number; qualification_tier?: string };
    decay?: { decay_bounded?: boolean; current_confidence?: number | string };
  };
  production_qualification?: {
    qualification_tier?: string;
    checks?: Record<string, boolean>;
    passed_count?: number;
    total_count?: number;
    summary?: string;
  };
  sustained_verification?: {
    sustained_qualified?: boolean;
    extended_monitoring_active?: boolean;
    summary?: string;
    drift_reverification?: { drift_bounded?: boolean; summary?: string };
    replay_stability?: { replay_stable?: boolean; summary?: string };
    verification?: { recurring_verification_active?: boolean; summary?: string };
  };
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

export const fetchProductionExecutionTruthState = () =>
  mcFetch<ProductionExecutionTruthState>("/api/v1/production-execution-truth/state");

export const fetchProductionExecutionTruthProviders = () =>
  mcFetch<ProductionExecutionTruthState["provider_truth"]>("/api/v1/production-execution-truth/providers");

export const fetchProductionExecutionTruthRollback = () =>
  mcFetch<ProductionExecutionTruthState["rollback_integrity"]>("/api/v1/production-execution-truth/rollback");

export const fetchProductionExecutionTruthStabilization = () =>
  mcFetch<ProductionExecutionTruthState["runtime_stabilization"]>("/api/v1/production-execution-truth/stabilization");

export const fetchProductionExecutionTruthInfrastructure = () =>
  mcFetch<ProductionExecutionTruthState["infrastructure_truth"]>("/api/v1/production-execution-truth/infrastructure");

export const fetchProductionExecutionTruthSustainedVerification = () =>
  mcFetch<ProductionExecutionTruthState["sustained_verification"]>(
    "/api/v1/production-execution-truth/sustained-verification",
  );

export const fetchProductionExecutionRealismState = () =>
  mcFetch<ProductionExecutionTruthState>("/api/v1/production-execution-realism/state");

export const fetchRealityHarnessV4 = () =>
  mcFetch<ProductionExecutionTruthState["harness"]>("/api/v1/reality-harness-v4/scenarios");
