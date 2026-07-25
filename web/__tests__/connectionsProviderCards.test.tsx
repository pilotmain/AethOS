import { describe, expect, it } from "vitest";

import {
  PLANNED_PROVIDERS,
  readonlyCapabilityCount,
  type ProviderCatalogEntry,
} from "@/lib/missionControl/providerCatalog";

describe("connectionsProviderCards", () => {
  it("lists planned providers for future cards", () => {
    expect(PLANNED_PROVIDERS).toEqual([]);
  });

  it("counts read-only capabilities for connected provider cards", () => {
    const vercel: ProviderCatalogEntry = {
      name: "vercel",
      label: "Vercel",
      connected: true,
      mutations_enabled: false,
      capabilities: {
        list_domains: {
          operation: "list_domains",
          read_only: true,
          mutation: false,
          api_supported: true,
          browser_fallback: false,
          browser_required: false,
          requires_approval: true,
          enabled: true,
        },
        redeploy: {
          operation: "redeploy",
          read_only: false,
          mutation: true,
          api_supported: false,
          browser_fallback: false,
          browser_required: false,
          requires_approval: true,
          enabled: false,
        },
      },
    };
    expect(readonlyCapabilityCount(vercel)).toBe(1);
  });
});
