import { describe, expect, it } from "vitest";

import { vercelCredentialsSaveUrl } from "@/lib/missionControl/connectionsApi";

describe("connectionsTokenSaveApiBase", () => {
  it("uses canonical API base for token save", () => {
    expect(vercelCredentialsSaveUrl()).toMatch(/\/api\/v1\/connections\/vercel\/credentials$/);
    expect(vercelCredentialsSaveUrl()).toMatch(/^http/);
  });
});
