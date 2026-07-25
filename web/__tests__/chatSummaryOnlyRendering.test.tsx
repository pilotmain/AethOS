import { describe, expect, it } from "vitest";

import { chatMessageLooksLikeSummaryOnly } from "@/lib/missionControl/jobArtifacts";

describe("chatSummaryOnlyRendering", () => {
  const fullReport =
    "# Competitor brief\n\n" +
    Array.from({ length: 40 }, (_, i) => `## Section ${i}\n\nLong paragraph ${i}.\n`).join("");

  it("treats summary-style completion as chat-safe", () => {
    const chatMsg = [
      "✅ Job completed — competitor brief ready",
      "",
      "Summary:",
      "- LangGraph analyzed",
      "- LangGraph noted",
      "",
      "Open Mission Control → Jobs for the full report.",
    ].join("\n");
    expect(chatMessageLooksLikeSummaryOnly(chatMsg, fullReport)).toBe(true);
    expect(chatMsg).not.toContain("## Section 39");
  });

  it("rejects messages that embed the full artifact", () => {
    expect(chatMessageLooksLikeSummaryOnly(fullReport, fullReport)).toBe(false);
  });
});
