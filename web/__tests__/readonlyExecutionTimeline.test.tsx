import { describe, expect, it } from "vitest";

import {
  executionDataSourceLabel,
  executionTimelineFromJob,
  readonlyExecutionBadge,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

const baseJob = (params: Record<string, unknown>): TrackedJobRecord =>
  ({
    id: "job-1",
    title: "Read-only execution",
    job_type: "readonly_execution_vercel",
    status: "completed",
    params,
  }) as TrackedJobRecord;

describe("readonlyExecutionTimeline", () => {
  it("renders execution timeline entries", () => {
    const timeline = executionTimelineFromJob(
      baseJob({
        execution_timeline: [{ status: "started", message: "Checking list deployments…" }],
      }),
    );
    expect(timeline).toHaveLength(1);
    expect(timeline[0].message).toMatch(/Checking/i);
  });
});

describe("readonlyExecutionBadges", () => {
  it("shows readonly badge", () => {
    expect(readonlyExecutionBadge(baseJob({ read_only: true }))).toMatch(/No mutation performed/i);
  });

  it("labels provider API execution", () => {
    expect(executionDataSourceLabel(baseJob({ data_source: "provider_api" }))).toBe(
      "Provider API execution",
    );
  });
});

describe("browserFallbackLabel", () => {
  it("labels browser fallback source", () => {
    expect(executionDataSourceLabel(baseJob({ data_source: "browser_fallback" }))).toMatch(
      /Browser fallback/i,
    );
  });
});
