import { describe, expect, it } from "vitest";

import { connectionStateLabel } from "@/lib/missionControl/connectionsCatalog";

describe("connectionsProviderCardsCatalog", () => {
  it("labels connection states for provider cards", () => {
    expect(connectionStateLabel("connected")).toBe("Connected");
    expect(connectionStateLabel("coming_soon")).toBe("Coming soon");
    expect(connectionStateLabel("backend_ready")).toBe("Backend ready");
  });
});
