/** Persisted agent session threads for Mission Control. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type SubagentMessage = {
  role?: string;
  content?: string;
  at?: number;
  source_tool?: string;
};

export type SubagentTranscriptStep = {
  step?: number;
  agent_id?: string;
  capability?: string;
  role_label?: string;
  attached_skills?: string[];
  summary?: string;
  status?: string;
};

export type SubagentSessionRow = {
  session_key: string;
  spawn_id?: string;
  parent_session_id?: string;
  goal?: string;
  role_label?: string;
  capability?: string;
  attached_skills?: string[];
  status?: string;
  run_count?: number;
  plan_id?: string | null;
  updated_at?: number;
  messages?: SubagentMessage[];
  transcript?: SubagentTranscriptStep[];
  terminal_preflight_ids?: string[];
};

export const fetchSubagentSessions = (parentSessionId?: string, limit = 50) => {
  const parent =
    parentSessionId && parentSessionId !== "all"
      ? `parent_session_id=${encodeURIComponent(parentSessionId)}&`
      : "";
  return mcFetch<{ ok: boolean; sessions: SubagentSessionRow[]; count: number }>(
    `/api/v1/agents/subagent-sessions?${parent}limit=${limit}`,
  );
};

export const fetchSubagentSession = (sessionKey: string) =>
  mcFetch<{ ok: boolean; session: SubagentSessionRow }>(
    `/api/v1/agents/subagent-sessions/${encodeURIComponent(sessionKey)}`,
  );

/** Messages whose content is plumbing/metadata, not a work deliverable. */
const OUTPUT_NOISE_TOOLS = new Set(["agent_spawn", "agent_creation"]);

/**
 * Pick the substantive textual deliverable to surface as "Latest output".
 *
 * The real work product is the coordination report (source_tool ===
 * "agent_coordination" — the "# Multi-agent operational intelligence report").
 * We must NOT show the trailing `agent_spawn` "Attached skills — …" line, which
 * is just spawn plumbing. Prefer the report; fall back to the most recent
 * substantive assistant message that isn't spawn/creation noise.
 */
export function pickLatestOutput(
  sessions: SubagentSessionRow[],
): { goal: string; content: string } | null {
  const completed = sessions.filter((s) =>
    ["complete", "done", "succeeded"].some((x) => (s.status ?? "").toLowerCase().includes(x)),
  );
  if (completed.length === 0) return null;
  const session = [...completed].sort((a, b) => (b.updated_at ?? 0) - (a.updated_at ?? 0))[0];
  const msgs = session.messages ?? [];
  const isAssistant = (m: SubagentMessage) => (m.role ?? "") !== "user";
  const report = [...msgs]
    .reverse()
    .find((m) => isAssistant(m) && m.source_tool === "agent_coordination" && (m.content ?? "").trim().length > 40);
  const fallback = [...msgs]
    .reverse()
    .find((m) => isAssistant(m) && !OUTPUT_NOISE_TOOLS.has(m.source_tool ?? "") && (m.content ?? "").trim().length > 60);
  const output = report ?? fallback;
  if (!output) return null;
  return { goal: session.goal ?? "Untitled", content: (output.content ?? "").trim() };
}
