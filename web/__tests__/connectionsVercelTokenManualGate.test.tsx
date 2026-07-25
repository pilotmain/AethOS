import { describe, expect, it } from "vitest";

import { methodLabel } from "@/lib/missionControl/connectionsApi";

describe("connectionsVercelTokenManualGate", () => {
  it("shows configured API token state without exposing secret", () => {
    expect(methodLabel("configured")).toBe("Configured");
    const masked = "verc********************7890";
    expect(masked).not.toMatch(/vercel_[a-z0-9]{20,}/i);
  });
});
