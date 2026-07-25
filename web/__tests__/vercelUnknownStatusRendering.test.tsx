import { describe, expect, it } from "vitest";

import type { VercelProjectRow } from "@/lib/missionControl/vercelArtifact";

export function healthLabelForProject(p: VercelProjectRow): string {
  const h = (p.health || "").toLowerCase();
  if (h === "unknown") return "production status unclear";
  if (h === "likely_healthy") return "likely healthy";
  if (h === "healthy") return "healthy";
  if (h === "failed") return p.attention_reason || "failed";
  return p.health || "unknown";
}

describe("vercelUnknownStatusRendering", () => {
  it("maps unknown health to operator-friendly label", () => {
    expect(
      healthLabelForProject({ name: "lifeos", health: "unknown" }),
    ).toBe("production status unclear");
  });

  it("does not label unknown as degraded", () => {
    const label = healthLabelForProject({ name: "wingman", health: "unknown" });
    expect(label).not.toContain("degraded");
    expect(label).not.toContain("no production");
  });
});
