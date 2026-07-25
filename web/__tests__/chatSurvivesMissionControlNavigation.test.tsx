import { beforeEach, describe, expect, it, vi } from "vitest";

import { formatChatError } from "@/lib/chat/lanes";
import { canSendChat, deriveChatHealth } from "@/lib/connection/chatHealth";
import { formatMcPanelError, mcFailureAffectsChat } from "@/lib/missionControl/panelError";
import { readCachedMessages, writeCachedMessages } from "@/lib/chat/lanes";

describe("chatSurvivesMissionControlNavigation", () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal("window", globalThis);
    const storage = {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
      removeItem: (key: string) => {
        delete store[key];
      },
      clear: () => {
        for (const k of Object.keys(store)) delete store[k];
      },
    };
    vi.stubGlobal("sessionStorage", storage);
    vi.stubGlobal("localStorage", storage);
  });

  it("persists chat history across navigation", () => {
    writeCachedMessages([
      { id: "1", role: "user", content: "hi" },
      { id: "2", role: "assistant", content: "Hello" },
    ]);
    const restored = readCachedMessages();
    expect(restored).toHaveLength(2);
    expect(restored[0]?.content).toBe("hi");
  });

  it("keeps chat send enabled when panel is degraded but chat_ready", () => {
    const health = deriveChatHealth({
      chat_ready: true,
      label: "Connected · Some panels delayed",
      panel: "degraded",
    });
    expect(canSendChat(health)).toBe(true);
  });

  it("MC endpoint failure does not set chat error patterns", () => {
    const mcErr = formatMcPanelError("Panel degraded");
    expect(mcFailureAffectsChat(mcErr)).toBe(false);
    expect(formatChatError("Mission Control request failed: 500")).not.toMatch(/panel degraded/i);
  });
});
