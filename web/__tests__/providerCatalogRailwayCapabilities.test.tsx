import { describe, expect, it } from "vitest";

import { readonlyCapabilityCount, type ProviderCatalogEntry } from "@/lib/missionControl/providerCatalog";

describe("providerCatalogRailwayCapabilities", () => {
  it("shows enabled readonly ops and keeps mutations disabled", () => {
    const entry: ProviderCatalogEntry = {
      name: "railway",
      label: "Railway",
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
    expect(readonlyCapabilityCount(entry)).toBe(2);
    expect(entry.capabilities.redeploy.enabled).toBe(false);
  });
});
