import { describe, expect, it } from "vitest";

import { usesProviderJobType } from "@/lib/missionControl/trackedJobs";

describe("providerJobLifecycle", () => {
  it("recognizes provider-backed job types", () => {
    expect(usesProviderJobType("comparison_brief")).toBe(true);
    expect(usesProviderJobType("checklist_generation")).toBe(false);
  });
});
