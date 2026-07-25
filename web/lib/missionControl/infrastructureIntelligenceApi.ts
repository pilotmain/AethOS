import { mcFetch } from "@/lib/missionControl/fetch";

export type InfrastructureCapability = {
  container_health?: string;
  restart_verification?: string;
  compose_topology?: string;
  runtime_pressure_analysis?: string;
  dependency_mapping?: string;
};

export type DockerRuntimeState = {
  ok: boolean;
  substrate: string;
  verified: boolean;
  maturity: string;
  verification_coverage_pct: number;
  capabilities: InfrastructureCapability;
  findings: string[];
  summary: string;
};

export type KubernetesRuntimeState = {
  ok: boolean;
  substrate: string;
  verified: boolean;
  maturity: string;
  verification_coverage_pct: number;
  summary: string;
  rollout?: { checks?: { check: string; status: string }[] };
  drift?: { drift_detected?: boolean; summary?: string };
};

export type InfrastructureTopologyState = {
  ok?: boolean;
  summary?: string;
  graph?: { summary?: string; node_count?: number; edge_count?: number };
  classifications?: { critical?: string[]; supporting?: string[] };
};

export type InfrastructureScenario = {
  id: string;
  name: string;
  substrate: string;
  verification: string[];
  status: string;
  coverage_pct: number;
  harness_version: string;
};

export type InfrastructureHarnessState = {
  ok: boolean;
  harness_version: string;
  scenario_count: number;
  verified_count: number;
  average_coverage_pct: number;
  scenarios: InfrastructureScenario[];
  summary: string;
};

export type InfrastructureIntelligenceState = {
  ok: boolean;
  phase: string;
  harness_version?: string;
  docker: DockerRuntimeState;
  kubernetes: KubernetesRuntimeState;
  topology?: InfrastructureTopologyState;
  confidence: { narrative: string; summary: string; confidence?: { infrastructure_truth_score?: number } };
  harness: InfrastructureHarnessState;
  capabilities: Record<string, string>;
  summary: string;
};

export const fetchInfrastructureState = () =>
  mcFetch<InfrastructureIntelligenceState>("/api/v1/infrastructure-intelligence/state");

export const fetchDockerRuntime = () =>
  mcFetch<DockerRuntimeState>("/api/v1/infrastructure-intelligence/docker");

export const fetchKubernetesRuntime = () =>
  mcFetch<KubernetesRuntimeState>("/api/v1/infrastructure-intelligence/kubernetes");

export const fetchInfrastructureHarness = () =>
  mcFetch<InfrastructureHarnessState>("/api/v1/infrastructure-intelligence/harness/scenarios");

export const fetchInfrastructureConfidence = () =>
  mcFetch<{ narrative: string; summary: string }>("/api/v1/infrastructure-intelligence/confidence");
