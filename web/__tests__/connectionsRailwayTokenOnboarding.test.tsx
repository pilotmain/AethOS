import { describe, expect, it } from "vitest";

import { providerCredentialsSaveUrl, vercelCredentialsSaveUrl } from "@/lib/missionControl/connectionsApi";
import {
  MANAGE_CREDENTIAL_PROVIDERS,
  providerCredentialConfig,
} from "@/lib/missionControl/providerCredentialConfig";

describe("connectionsRailwayTokenOnboarding", () => {
  it("includes railway in manage credential providers", () => {
    expect(MANAGE_CREDENTIAL_PROVIDERS).toContain("railway");
    expect(MANAGE_CREDENTIAL_PROVIDERS).toContain("github");
    expect(MANAGE_CREDENTIAL_PROVIDERS).toContain("vercel");
  });

  it("uses generalized save URL for railway", () => {
    expect(providerCredentialsSaveUrl("railway")).toMatch(/\/api\/v1\/connections\/railway\/credentials$/);
    expect(vercelCredentialsSaveUrl()).toBe(providerCredentialsSaveUrl("vercel"));
  });

  it("defines railway onboarding copy without token placeholders", () => {
    const cfg = providerCredentialConfig("railway");
    expect(cfg).not.toBeNull();
    expect(cfg?.description).toMatch(/read-only/i);
    expect(cfg?.securityNote).toMatch(/never displays saved tokens/i);
    expect(cfg?.supportsPreferredAuth).toBe(false);
  });
});
