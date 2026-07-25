import { describe, expect, it } from "vitest";

import {
  browserActionDetail,
  isBrowserActionType,
} from "@/lib/settings/browserCapability";

describe("browserJobProposal", () => {
  it("identifies browser actions and supervised target copy", () => {
    const action = {
      action_type: "browser_navigation_plan",
      params: { target: "vercel.com", mode: "supervised" },
    };
    expect(isBrowserActionType(action.action_type)).toBe(true);
    expect(browserActionDetail(action)).toMatch(/Target: vercel.com/);
    expect(browserActionDetail(action)).toMatch(/Approval required/);
  });

  it("non-browser actions are not labeled as browser proposals", () => {
    expect(isBrowserActionType("vercel_cli_probe")).toBe(false);
    expect(
      browserActionDetail({
        action_type: "vercel_cli_probe",
        params: {},
      }),
    ).toBeNull();
  });
});
