import { describe, expect, it } from "vitest";

describe("browserSessionClose", () => {
  it("close endpoint path is stable for MC panel", () => {
    const sid = "bsess-abc123";
    const path = `/api/v1/browser/sessions/${encodeURIComponent(sid)}/close`;
    expect(path).toBe("/api/v1/browser/sessions/bsess-abc123/close");
  });
});
