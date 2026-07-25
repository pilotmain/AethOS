import { describe, expect, it } from "vitest";

import {
  operationalSignalClass,
  operationalSignalStyle,
} from "@/lib/missionControl/signalHierarchy";

describe("missionControlSignalHierarchy", () => {
  it("defines four signal levels", () => {
    expect(Object.keys(operationalSignalClass)).toEqual([
      "dominant",
      "reassurance",
      "continuity",
      "whisper",
    ]);
  });

  it("dominant signal has strongest weight", () => {
    const dominant = operationalSignalStyle.dominant;
    const whisper = operationalSignalStyle.whisper;
    expect(Number(dominant.fontWeight)).toBeGreaterThan(Number(whisper.fontWeight ?? 0));
  });

  it("maps signal levels to css classes", () => {
    expect(operationalSignalClass.dominant).toBe("mc-signal-dominant");
    expect(operationalSignalClass.whisper).toBe("mc-signal-whisper");
  });
});
