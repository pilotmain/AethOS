import { mcFetch } from "@/lib/missionControl/fetch";

export type SynthesisScenario = {
  id: string;
  name: string;
  validation?: string[];
  status: string;
  coverage_pct: number;
};

export type ConversationalIntelligenceState = {
  ok: boolean;
  phase: string;
  harness_version?: string;
  qualification_tier?: string;
  capabilities?: Record<string, string>;
  sample_synthesis?: { reply?: string; verified?: boolean; contract?: { result_count?: number } };
  harness?: {
    scenario_count: number;
    verified_count: number;
    average_coverage_pct: number;
    scenarios: SynthesisScenario[];
  };
  summary?: string;
};

export const fetchConversationalIntelligenceState = () =>
  mcFetch<ConversationalIntelligenceState>("/api/v1/conversational-intelligence/state");

export const fetchSynthesisHarness = () =>
  mcFetch<ConversationalIntelligenceState["harness"]>("/api/v1/conversational-intelligence/harness/scenarios");
