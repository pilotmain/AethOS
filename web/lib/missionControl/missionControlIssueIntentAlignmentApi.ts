/** FIX 184 — issue intent alignment (validation ≠ patch execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type IssueIntentAlignmentResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  patch_execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  autonomous_scope_expansion_enabled: boolean;
  autonomous_file_selection_override_enabled: boolean;
  autonomous_authority_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  alignment_validation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  issue_intent_alignment?: Record<string, unknown>;
  markdown?: string;
};

export type IssueIntentAlignmentRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  issue_intent_alignment_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlIssueIntentAlignment = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<IssueIntentAlignmentResponse>(
    `/api/v1/mission-control/issue-intent-alignment?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlIssueIntentAlignmentRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<IssueIntentAlignmentRecordResponse>(
    `/api/v1/mission-control/issue-intent-alignment/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
