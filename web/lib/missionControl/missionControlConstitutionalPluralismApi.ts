/** FIX 162 — constitutional pluralism + governance perspective (constitutional pluralism cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ConstitutionalPluralismResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  authoritative_worldview_selection_enabled: boolean;
  autonomous_constitutional_arbitration_enabled: boolean;
  enforced_ideological_alignment_enabled: boolean;
  sovereignty_delegation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  constitutional_pluralism?: Record<string, unknown>;
  markdown?: string;
};

export type ConstitutionalPluralismRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  constitutional_pluralism_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlConstitutionalPluralism = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ConstitutionalPluralismResponse>(
    `/api/v1/mission-control/constitutional-pluralism?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlConstitutionalPluralismRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<ConstitutionalPluralismRecordResponse>(
    `/api/v1/mission-control/constitutional-pluralism/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
