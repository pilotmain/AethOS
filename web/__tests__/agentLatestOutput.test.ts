import { describe, expect, it } from "vitest";

import { pickLatestOutput, type SubagentSessionRow } from "@/lib/missionControl/subagentSessionsApi";

/**
 * Locks the "Latest output" selection on the Agents (Orchestration) panel.
 * The substantive deliverable is the coordination report — NOT the trailing
 * `agent_spawn` "Attached skills — …" plumbing line. A real screenshot showed
 * the card grabbing that noise; these tests stop it regressing.
 */
const report =
  "# Multi-agent operational intelligence report (governed)\n\n" +
  "**Goal:** summarize deployment risks\n**Status:** completed\n**Severity:** LOW\n**Confidence:** low\n\n" +
  "## Evidence\n- `aart-aa508` — opera";
const skillsNoise = "Attached skills — operations_analyst: summarize_failures, correlate_evidence, operational_timeline";

function session(over: Partial<SubagentSessionRow>): SubagentSessionRow {
  return { session_key: "s1", status: "completed", goal: "summarize deployment risks", updated_at: 100, ...over };
}

describe("pickLatestOutput", () => {
  it("prefers the coordination report over trailing agent_spawn skills noise", () => {
    const out = pickLatestOutput([
      session({
        messages: [
          { role: "user", content: "summarize deployment risks", source_tool: "agent_send" },
          { role: "assistant", content: report, source_tool: "agent_coordination" },
          { role: "assistant", content: skillsNoise, source_tool: "agent_spawn" }, // comes LAST but is noise
        ],
      }),
    ]);
    expect(out).not.toBeNull();
    expect(out!.content).toContain("operational intelligence report");
    expect(out!.content).not.toContain("Attached skills");
  });

  it("returns null when no session has completed", () => {
    expect(pickLatestOutput([session({ status: "running", messages: [{ role: "assistant", content: report }] })])).toBeNull();
    expect(pickLatestOutput([])).toBeNull();
  });

  it("picks the most recently updated completed session", () => {
    const out = pickLatestOutput([
      session({ session_key: "old", updated_at: 10, goal: "old goal", messages: [{ role: "assistant", content: report, source_tool: "agent_coordination" }] }),
      session({ session_key: "new", updated_at: 999, goal: "new goal", messages: [{ role: "assistant", content: report, source_tool: "agent_coordination" }] }),
    ]);
    expect(out!.goal).toBe("new goal");
  });

  it("falls back to a substantive assistant message when there's no coordination report", () => {
    const longAnswer = "Here are the three biggest deployment risks: cold starts, missing env vars, and DB connection limits.";
    const out = pickLatestOutput([
      session({
        messages: [
          { role: "user", content: "summarize deployment risks", source_tool: "agent_send" },
          { role: "assistant", content: longAnswer, source_tool: "agent_send" },
          { role: "assistant", content: skillsNoise, source_tool: "agent_spawn" }, // still ignored as noise
        ],
      }),
    ]);
    expect(out!.content).toBe(longAnswer);
  });

  it("never surfaces spawn/creation plumbing as the output", () => {
    const out = pickLatestOutput([
      session({
        messages: [
          { role: "assistant", content: "agent created", source_tool: "agent_creation" },
          { role: "assistant", content: skillsNoise, source_tool: "agent_spawn" },
        ],
      }),
    ]);
    expect(out).toBeNull(); // only noise → nothing worth showing
  });
});
