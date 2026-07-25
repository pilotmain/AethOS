import { describe, expect, it } from "vitest";

import { formatOperationalEventAt } from "@/lib/missionControl/operationPreflight";

describe("executionTimelineTimestampFormatting", () => {
  it("formats epoch milliseconds for display", () => {
    const label = formatOperationalEventAt(1776884598019);
    expect(label).toContain("UTC");
  });
});
