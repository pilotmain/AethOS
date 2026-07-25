import { describe, expect, it } from "vitest";

import {
  MC_CONTENT_MAX_WIDTH,
  MC_SIDEBAR_WIDTH,
  MISSION_CONTROL_SCROLL_MAIN_ATTR,
  MISSION_CONTROL_SCROLL_ROOT_ATTR,
  artifactReportPreStyle,
  missionControlAppShellStyle,
  missionControlContentCanvasStyle,
  missionControlScrollMainStyle,
} from "@/lib/missionControl/layout";

describe("missionControlScrollableLayout", () => {
  it("uses a full-viewport flex shell with sidebar + main column", () => {
    expect(missionControlAppShellStyle.display).toBe("flex");
    expect(missionControlAppShellStyle.minHeight).toBe("100vh");
    expect(MC_SIDEBAR_WIDTH).toBe(240);
    expect(MC_CONTENT_MAX_WIDTH).toBeGreaterThanOrEqual(1280);
  });

  it("exposes data attributes for scroll root and main (regression anchors)", () => {
    expect(MISSION_CONTROL_SCROLL_ROOT_ATTR).toBe("data-mc-scroll-root");
    expect(MISSION_CONTROL_SCROLL_MAIN_ATTR).toBe("data-mc-scroll-main");
  });

  it("uses wide content canvas instead of narrow centered column", () => {
    expect(missionControlContentCanvasStyle.maxWidth).toBe(1400);
    expect(missionControlContentCanvasStyle.width).toBe("100%");
  });

  it("keeps dedicated scroll main region", () => {
    expect(missionControlScrollMainStyle.flex).toBe(1);
    expect(missionControlScrollMainStyle.overflowY).toBe("auto");
    expect(missionControlScrollMainStyle.minHeight).toBe(0);
  });

  it("does not trap artifact reports in a fixed-height inner scroll panel", () => {
    expect(artifactReportPreStyle.maxHeight).toBeUndefined();
    expect(artifactReportPreStyle.overflow).toBeUndefined();
  });
});
