import { describe, expect, it } from "vitest";

import { chatMessageLooksLikeSummaryOnly } from "@/lib/missionControl/jobArtifacts";

describe("externalHealthJobChat", () => {
  const fullReport =
    "# Vercel external health report\n\n" +
    Array.from({ length: 50 }, (_, i) => `## Source ${i}\n\nDetail ${i}\n`).join("");

  it("completion bubble stays summary-only for external health jobs", () => {
    const chatMsg = [
      "✅ Job completed — Vercel health report ready",
      "",
      "Summary:",
      "- Public status source checked",
      "- CLI availability noted (approval required to run commands)",
      "",
      "Open Mission Control → Jobs for the full report.",
    ].join("\n");
    expect(chatMessageLooksLikeSummaryOnly(chatMsg, fullReport)).toBe(true);
  });
});
