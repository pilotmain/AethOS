/** FIX 240 — repository knowledge graph (repository_intelligence ≠ repository_authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type RepositoryKnowledgeGraphResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  repository_compose_evidence_only: boolean;
  repository_authority: boolean;
  code_modification_authority: boolean;
  cross_repo_authority: boolean;
  knowledge_graph_execution: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  rollback_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  repository_knowledge_graph?: Record<string, unknown>;
  markdown?: string;
};

export type RepositoryKnowledgeGraphRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  repository_knowledge_graph_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlRepositoryKnowledgeGraph = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<RepositoryKnowledgeGraphResponse>(
    `/api/v1/mission-control/repository-knowledge-graph?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlRepositoryKnowledgeGraphRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata: Record<string, unknown> = {},
) =>
  mcFetch<RepositoryKnowledgeGraphRecordResponse>(
    `/api/v1/mission-control/repository-knowledge-graph/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author, metadata }),
    },
  );
