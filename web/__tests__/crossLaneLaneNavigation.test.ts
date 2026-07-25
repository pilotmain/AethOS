import { describe, expect, it } from "vitest";

import {
  buildLaneDetailBlock,
  laneAnchorId,
  laneDataFromSnapshot,
} from "@/lib/missionControl/crossLaneLaneNavigation";
import type { MissionControlCrossLaneSnapshot } from "@/lib/missionControl/missionControlCrossLaneApi";

describe("crossLaneLaneNavigation", () => {
  it("builds stable lane anchor ids", () => {
    expect(laneAnchorId("software_delivery")).toBe("mc-lane-software-delivery");
    expect(laneAnchorId("railway_orchestration")).toBe("mc-lane-railway-orchestration");
  });

  it("resolves lane data from snapshot aliases", () => {
    const snapshot: MissionControlCrossLaneSnapshot = {
      lanes: {
        software_delivery: { plan_id: "plan-1", ok: true },
      },
      incident_linkage: { open_incidents: 2, ok: true },
    };
    expect(laneDataFromSnapshot(snapshot, "software_delivery").plan_id).toBe("plan-1");
    expect(laneDataFromSnapshot(snapshot, "incident_command").open_incidents).toBe(2);
  });

  it("builds software delivery detail rows", () => {
    const snapshot: MissionControlCrossLaneSnapshot = {
      lanes: {
        software_delivery: {
          plan_id: "p-9",
          plan_status: "planning_approved",
          pending_gates: ["workspace_verification"],
          timeline_event_count: 3,
        },
      },
    };
    const block = buildLaneDetailBlock(snapshot, "software_delivery");
    expect(block.anchorId).toBe("mc-lane-software-delivery");
    expect(block.rows.some((r) => r.label === "Plan id" && r.value === "p-9")).toBe(true);
  });
});
