import { describe, expect, it } from "vitest";

import { methodLabel } from "@/lib/missionControl/connectionsApi";

describe("connectionsSettingsPanel", () => {
  it("labels connection method states", () => {
    expect(methodLabel("configured")).toBe("Configured");
    expect(methodLabel("missing")).toBe("Missing");
    expect(methodLabel("saved")).toBe("Saved");
  });
});
