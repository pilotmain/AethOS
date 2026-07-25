import { describe, expect, it } from "vitest";

import { readonlyCapabilityCount, type ProviderCatalogEntry } from "@/lib/missionControl/providerCatalog";

describe("providerCapabilityRendering", () => {
  it("derives capability summary for provider cards", () => {
    const entry: ProviderCatalogEntry = {
      name: "vercel",
      label: "Vercel",
      connected: true,
      mutations_enabled: false,
      capabilities: {
        list_deployments: {
          operation: "list_deployments",
          read_only: true,
          mutation: false,
          api_supported: true,
          browser_fallback: false,
          browser_required: false,
          requires_approval: true,
          enabled: true,
        },
        why_down: {
          operation: "why_down",
          read_only: true,
          mutation: false,
          api_supported: "partial",
          browser_fallback: "fallback",
          browser_required: false,
          requires_approval: true,
          enabled: true,
        },
      },
    };
    expect(readonlyCapabilityCount(entry)).toBe(2);
  });
});
