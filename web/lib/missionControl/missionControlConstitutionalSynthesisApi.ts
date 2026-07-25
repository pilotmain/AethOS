/** FIX 163 — constitutional synthesis + institutional wisdom (synthesis cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ConstitutionalSynthesisResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_constitutional_decisions_enabled: boolean;
  doctrine_enforcement_enabled: boolean;
  legitimacy_arbitration_enabled: boolean;
  worldview_selection_enabled: boolean;
  sovereignty_delegation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  constitutional_synthesis?: Record<string, unknown>;
  markdown?: string;
};

export type ConstitutionalSynthesisRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  constitutional_synthesis_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlConstitutionalSynthesis = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ConstitutionalSynthesisResponse>(
    `/api/v1/mission-control/constitutional-synthesis?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlConstitutionalSynthesisRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<ConstitutionalSynthesisRecordResponse>(
    `/api/v1/mission-control/constitutional-synthesis/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
