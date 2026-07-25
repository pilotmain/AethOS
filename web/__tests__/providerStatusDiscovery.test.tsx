import { describe, expect, it } from "vitest";

import {
  providerTopologyFromInventory,
  providerTopologyLabel,
} from "@/lib/missionControl/providerDiscovery";

describe("providerStatusDiscovery", () => {
  it("renders discovered Railway topology", () => {
    const topology = providerTopologyFromInventory({
      provider: "railway",
      projects: [
        {
          name: "atlas-trader",
          id: "proj-1",
          environments: [
            {
              name: "production",
              id: "env-prod",
              services: [
                { name: "api", id: "svc-api", status: "online", domain: "api.example.app" },
                { name: "worker", id: "svc-worker", status: "online" },
                { name: "redis", id: "svc-redis", status: "online" },
                { name: "postgres", id: "svc-pg", status: "online" },
              ],
            },
          ],
        },
      ],
      freshness: "fresh",
    });
    expect(topology).not.toBeNull();
    expect(topology?.groups[0]?.services.map((s) => s.name)).toEqual(["api", "worker", "redis", "postgres"]);
    expect(providerTopologyLabel(topology!)).toContain("atlas-trader / production");
  });
});
