import { describe, expect, it } from "vitest";

import {
  vercelAuthMethodLabel,
  vercelAuthRef,
  vercelInspectionCompletionCopy,
} from "@/lib/missionControl/vercelAuthMethod";

describe("vercelInventoryAuthMethodRendering", () => {
  it("labels API token jobs without browser session wording", () => {
    expect(
      vercelAuthMethodLabel({
        auth_method: "api_token",
        auth_method_label: "Vercel API token",
      }),
    ).toBe("Vercel API token");
    expect(
      vercelInspectionCompletionCopy("api_token"),
    ).toMatch(/saved Vercel API token/i);
    expect(vercelInspectionCompletionCopy("api_token")).not.toMatch(/browser session/i);
  });

  it("labels browser session jobs correctly", () => {
    expect(vercelAuthMethodLabel({ auth_method: "browser" })).toBe("Saved browser session");
    expect(vercelInspectionCompletionCopy("browser")).toMatch(/saved browser session/i);
    expect(vercelAuthRef({ auth_method: "browser", profile_id: "bprof-1" })).toBe("bprof-1");
  });

  it("prefers credential id for API token auth ref", () => {
    expect(
      vercelAuthRef({ auth_method: "api_token", credential_id: "cred-abc" }),
    ).toBe("cred-abc");
  });
});
