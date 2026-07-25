import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  mergeBrowserLifecycleEvents,
  pruneSeenBrowserToDisplayed,
  readSeenBrowserEventIds,
  writeSeenBrowserEventIds,
} from "@/lib/chat/browserLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";
import type { BrowserSessionEventRecord } from "@/lib/missionControl/browserSessions";

const completed: BrowserSessionEventRecord = {
  id: "bsess-1:session_completed",
  session_id: "bsess-1",
  event_type: "session_completed",
  message: "✅ Browser session completed — vercel.com",
  status: "completed",
  target: "vercel.com",
  chat_session_id: "default",
  at: 3,
};

function stubSessionStorage() {
  const store: Record<string, string> = {};
  vi.stubGlobal("window", globalThis);
  vi.stubGlobal("sessionStorage", {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => {
      store[k] = v;
    },
  });
}

describe("browserSessionPollerSeenState", () => {
  beforeEach(() => {
    stubSessionStorage();
  });

  it("persists seen event ids in sessionStorage", () => {
    const merged = mergeBrowserLifecycleEvents([], [completed], new Set());
    writeSeenBrowserEventIds(merged.seen);
    const stored = readSeenBrowserEventIds();
    expect(stored.has("bsess-1:session_completed")).toBe(true);
    expect(stored.has("bsess-1:session_completed".replace(/^bsess-1/, "bsess-1"))).toBe(true);
  });

  it("pruneSeenBrowserToDisplayed keeps seen ids that match rendered bubbles", () => {
    const messages: CachedMessage[] = [
      {
        id: "bsess-evt-bsess-1:session_completed",
        role: "system",
        content: completed.message,
      },
    ];
    const seen = new Set(["bsess-1:session_completed", "bsess-1:session_completed"]);
    const pruned = pruneSeenBrowserToDisplayed(messages, seen);
    expect(pruned.has("bsess-1:session_completed")).toBe(true);
  });

  it("simulates three polls without adding duplicate bubbles", () => {
    let messages: CachedMessage[] = [];
    let seen = new Set<string>();
    for (let i = 0; i < 3; i++) {
      seen = pruneSeenBrowserToDisplayed(messages, readSeenBrowserEventIds());
      const merged = mergeBrowserLifecycleEvents(messages, [completed], seen);
      if (merged.added > 0) {
        writeSeenBrowserEventIds(merged.seen);
        messages = merged.messages;
      }
    }
    expect(messages.filter((m) => m.role === "system")).toHaveLength(1);
  });
});
