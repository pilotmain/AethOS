/** FIX 185 — issue intake scope fidelity (readonly plan envelope). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type IssueIntakeScopeFidelityResponse = {
  ok: boolean;
  session_id: string;
  fix?: string;
  read_only?: boolean;
  schema_version?: string;
  issue_intake_scope_fidelity?: Record<string, unknown>;
  assessment?: Record<string, unknown>;
  expected_targets_for_fix_184?: string[];
  detail?: string;
};

export const fetchMissionControlIssueIntakeScopeFidelity = (sessionId = "operator") =>
  mcFetch<IssueIntakeScopeFidelityResponse>(
    `/api/v1/mission-control/issue-intake-scope-fidelity?session_id=${encodeURIComponent(sessionId)}`,
  );
