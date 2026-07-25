import { describe, expect, it } from "vitest";

import type { CatalogChannelEntry } from "@/lib/missionControl/connectionsCatalog";
import { formatActivityTimestamp, transportHealthLabel } from "@/lib/missionControl/connectionsCatalog";
import { tokenSourceLabel } from "@/lib/missionControl/channelsApi";

describe("connectionsCatalog channel helpers", () => {
  it("labels transport health states", () => {
    expect(transportHealthLabel("ok")).toBe("Transport OK");
    expect(transportHealthLabel("token_missing")).toBe("Token missing");
    expect(transportHealthLabel("disabled")).toBe("Disabled");
  });

  it("formats activity timestamps", () => {
    expect(formatActivityTimestamp(null)).toBe("Never");
    expect(formatActivityTimestamp(undefined)).toBe("Never");
    expect(formatActivityTimestamp(1_700_000_000)).toContain("2023");
  });

  it("telegram catalog entry shape supports health card fields", () => {
    const channel: CatalogChannelEntry = {
      name: "telegram",
      label: "Telegram",
      token_configured: true,
      token_source: "vault",
      transport_health: "ok",
      webhook_path: "/api/v1/channels/telegram/webhook",
      active_chats_count: 2,
    };
    expect(channel.token_configured).toBe(true);
    expect(tokenSourceLabel(channel.token_source)).toBe("Credential vault");
    expect(channel.webhook_path).toContain("telegram");
  });
});
