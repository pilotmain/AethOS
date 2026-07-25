import { describe, expect, it } from "vitest";

import type { BrowserProfileRecord } from "@/lib/missionControl/browserProfiles";

describe("browserProfilesPanel", () => {
  it("public profile records hide storage secrets", () => {
    const profile: BrowserProfileRecord = {
      profile_id: "bprof-abc",
      site: "vercel.com",
      scope: "vercel",
      storage_path: "(local profile data — not shown)",
      created_at: 1,
      user_approved_persistence: true,
      status: "active",
      read_only_allowed: true,
      write_actions_allowed: false,
    };
    expect(profile.write_actions_allowed).toBe(false);
    expect(profile.read_only_allowed).toBe(true);
    expect(profile.storage_path).not.toMatch(/eyJ/);
    expect(profile.storage_path).toContain("not shown");
  });
});
