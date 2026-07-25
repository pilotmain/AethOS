import { describe, expect, it } from "vitest";

import { providerServicePickerOptions } from "@/lib/missionControl/providerDiscovery";

describe("runtimeActionsProviderPicker", () => {
  it("builds provider service picker options from inventory", () => {
    const options = providerServicePickerOptions({
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
                { name: "api", id: "svc-api", status: "online" },
                { name: "worker", id: "svc-worker", status: "online" },
              ],
            },
          ],
        },
      ],
    });
    expect(options).toHaveLength(2);
    expect(options[0]?.label).toContain("atlas-trader / production / api");
    expect(options[1]?.value).toBe("svc-worker");
  });
});
