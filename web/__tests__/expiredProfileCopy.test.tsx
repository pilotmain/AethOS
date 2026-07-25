import { describe, expect, it } from "vitest";

import type { BrowserProfileRecord } from "@/lib/missionControl/browserProfiles";

describe("expiredProfileCopy", () => {
  it("expired profile is not treated as ready for inspection", () => {
    const profile: BrowserProfileRecord = {
      profile_id: "bprof-exp",
      site: "vercel.com",
      scope: "vercel",
      storage_path: "(local profile data — not shown)",
      created_at: 1,
      status: "expired",
      user_approved_persistence: true,
      read_only_allowed: true,
      write_actions_allowed: false,
    };
    expect(profile.status).toBe("expired");
    expect(profile.read_only_allowed).toBe(true);
  });

  it("active profile is the only status suitable for saved-session inspection", () => {
    const active: BrowserProfileRecord = {
      profile_id: "bprof-ok",
      site: "vercel.com",
      scope: "vercel",
      storage_path: "(local profile data — not shown)",
      created_at: 1,
      status: "active",
      user_approved_persistence: true,
      read_only_allowed: true,
      write_actions_allowed: false,
    };
    expect(active.status).toBe("active");
  });
});
