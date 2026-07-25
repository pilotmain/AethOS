/** Multi-agent runtime — Mission Control agents section. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AgentSpec = {
  agent_id: string;
  label: string;
  purpose: string;
  allowed: string[];
  blocked: string[];
  /** Capability the orchestrator narrows a spawn down to (on-demand model). */
  capability?: string;
  /** True when this is a composable capability, not a standing agent. */
  on_demand?: boolean;
};

export type AgentArtifact = {
  artifact_id: string;
  artifact_type: string;
  agent_id?: string | null;
  plan_id?: string | null;
  created_at?: number;
  summary?: string;
  payload?: Record<string, unknown>;
};

export type CoordinationEvent = {
  at?: number;
  plan_id?: string;
  goal?: string;
  status?: string;
  artifact_id?: string;
};

export type AgentsListResponse = {
  ok: boolean;
  agents: AgentSpec[];
  artifacts: AgentArtifact[];
  coordination_memory: {
    coordination_events?: CoordinationEvent[];
    task_memory?: Record<string, unknown>;
  };
};

export type AgentSpawnResult = {
  ok: boolean;
  spawn_id?: string;
  session_key?: string;
  error?: string;
  hint?: string;
  agent_count?: number;
  status?: string;
};

/** §7 — delegate a task from the orchestration board (flag-gated server-side). */
export const delegateAgentSpawn = (goal: string, parentSessionId = "operator") =>
  mcFetch<AgentSpawnResult>("/api/v1/agents/spawn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, parent_session_id: parentSessionId }),
  });

export const fetchAgents = () => mcFetch<AgentsListResponse>("/api/v1/agents");

export const fetchAgentArtifacts = (limit = 40) =>
  mcFetch<{ ok: boolean; artifacts: AgentArtifact[] }>(`/api/v1/agents/artifacts?limit=${limit}`);

export const fetchAgentArtifact = (artifactId: string) =>
  mcFetch<{ ok: boolean; artifact: AgentArtifact & { payload?: Record<string, unknown> } }>(
    `/api/v1/agents/artifacts/${artifactId}`,
  );
