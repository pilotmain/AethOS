/** FIX 141 — mission knowledge spaces semantic search (read-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type KnowledgeSpacesSearchPayload = {
  query: string;
  focal_space_id?: string;
  knowledge_space_count: number;
  document_corpus_size: number;
  search_results: Array<Record<string, unknown>>;
  seen_before: Record<string, unknown>;
  related_missions: Array<Record<string, unknown>>;
  recommendations: Array<{ kind?: string; recommendation?: string; executable?: boolean }>;
  operational_context_recall: Record<string, unknown>;
};

export type KnowledgeSpacesSearchResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_action_enabled: boolean;
  automatic_mutation_planning_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  search?: KnowledgeSpacesSearchPayload;
  markdown?: string;
};

export const fetchMissionControlKnowledgeSpacesSearch = (
  sessionId: string,
  query: string,
  format: "json" | "markdown" | "both" = "both",
  opts?: { spaceId?: string; category?: string; ingestCurrent?: boolean; limit?: number },
) => {
  const params = new URLSearchParams({ session_id: sessionId, q: query, format });
  if (opts?.spaceId) params.set("space_id", opts.spaceId);
  if (opts?.category) params.set("category", opts.category);
  if (opts?.ingestCurrent === false) params.set("ingest_current", "false");
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  return mcFetch<KnowledgeSpacesSearchResponse>(
    `/api/v1/mission-control/knowledge-spaces/search?${params.toString()}`,
  );
};
