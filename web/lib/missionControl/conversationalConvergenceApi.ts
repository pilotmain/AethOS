import { mcFetch } from "@/lib/missionControl/fetch";

export type ConversationalConvergenceState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  qualification_tier?: string;
  summary?: string;
  reliability?: {
    reply?: string;
    verified?: boolean;
    items?: unknown[];
    contract?: { result_count?: number };
    integrity?: { clean?: boolean };
  };
  harness?: {
    scenario_count: number;
    verified_count: number;
    average_coverage_pct: number;
  };
  interaction_layers?: {
    layers: Record<string, { label: string; behavior: string; telemetry_allowed: boolean; artifacts_visible: boolean }>;
    principle?: string;
  };
  trust_maturity?: {
    trust_maturity_score?: number;
    trust_maturity_level?: string;
    summary?: string;
  };
  synthesis_consistency?: {
    consistency_score?: number;
    synthesis_consistent?: boolean;
    summary?: string;
  };
  production_interaction?: {
    qualified?: boolean;
    qualification_tier?: string;
    checks?: Record<string, boolean>;
    passed_count?: number;
    total_count?: number;
    summary?: string;
  };
  maturity_profile?: {
    profile?: Record<string, string>;
    strategic_position?: string;
    category_direction?: string;
    summary?: string;
  };
  principles?: Record<string, string>;
};

export const fetchConversationalConvergenceState = () =>
  mcFetch<ConversationalConvergenceState>("/api/v1/conversational-convergence/state");

export const fetchInteractionLayers = () =>
  mcFetch<ConversationalConvergenceState["interaction_layers"]>("/api/v1/conversational-convergence/layers");
