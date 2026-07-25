import { mcFetch } from "@/lib/missionControl/fetch";

export type QualificationDimension = {
  status: string;
  passed: boolean;
};

export type ConversationalReliabilityState = {
  ok: boolean;
  phase: string;
  production_qualified?: boolean;
  harness_version?: string;
  qualification_tier?: string;
  verified?: boolean;
  capabilities?: Record<string, string>;
  sample?: { reply?: string; verified?: boolean; contract?: { result_count?: number }; items?: unknown[] };
  harness?: {
    scenario_count: number;
    verified_count: number;
    average_coverage_pct: number;
    scenarios: { id: string; name: string; status: string; coverage_pct: number }[];
  };
  qualification?: {
    dimensions?: Record<string, QualificationDimension>;
    passed_count?: number;
    total_count?: number;
    qualified?: boolean;
    summary?: string;
  };
  trust_integrity?: { trust_integrity_ok?: boolean; summary?: string };
  human_interaction_reliability?: { production_qualified?: boolean; summary?: string };
  strategic_position?: {
    convergence_status?: Record<string, string>;
    next_frontier?: string;
    summary?: string;
  };
  principles?: Record<string, string>;
  summary?: string;
};

export const fetchConversationalReliabilityState = () =>
  mcFetch<ConversationalReliabilityState>("/api/v1/conversational-reliability/state");

export const fetchConversationalQualificationState = () =>
  mcFetch<ConversationalReliabilityState>("/api/v1/conversational-qualification/state");

export const fetchConversationalHarness = () =>
  mcFetch<ConversationalReliabilityState["harness"]>("/api/v1/conversational-reliability/harness/scenarios");
