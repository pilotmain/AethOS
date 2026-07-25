/** FIX 159 — constitutional ethics + institutional moral reasoning (constitutional ethical cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ConstitutionalEthicsResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_moral_authority_enabled: boolean;
  self_authored_ethics_enabled: boolean;
  constitutional_override_authority_enabled: boolean;
  value_enforcement_authority_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  constitutional_ethics?: Record<string, unknown>;
  markdown?: string;
};

export type ConstitutionalEthicsRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  constitutional_ethics_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlConstitutionalEthics = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ConstitutionalEthicsResponse>(
    `/api/v1/mission-control/constitutional-ethics?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlConstitutionalEthicsRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<ConstitutionalEthicsRecordResponse>(
    `/api/v1/mission-control/constitutional-ethics/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
