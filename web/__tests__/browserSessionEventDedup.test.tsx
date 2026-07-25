import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  browserEventDedupeKey,
  mergeBrowserLifecycleEvents,
  readSeenBrowserEventIds,
  writeSeenBrowserEventIds,
} from "@/lib/chat/browserLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";
import type { BrowserSessionEventRecord } from "@/lib/missionControl/browserSessions";

const launching: BrowserSessionEventRecord = {
  id: "bsess-1:session_launching",
  session_id: "bsess-1",
  event_type: "session_launching",
  message: "⏳ Browser session launching — vercel.com…",
  status: "launching",
  target: "vercel.com",
  chat_session_id: "default",
  at: 1,
};

const opened: BrowserSessionEventRecord = {
  id: "bsess-1:session_running",
  session_id: "bsess-1",
  event_type: "session_running",
  message: "🌐 Browser session opened — vercel.com",
  status: "running",
  target: "vercel.com",
  chat_session_id: "default",
  at: 2,
};

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

describe("browserSessionEventDedup", () => {
  beforeEach(() => {
    stubSessionStorage();
  });

  it("does not append launching/running from browser poller (action bridge owns those)", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "open vercel" }];
    const merged = mergeBrowserLifecycleEvents(base, [launching, opened], new Set());
    expect(merged.added).toBe(0);
    expect(merged.messages).toHaveLength(1);
  });

  it("repeated poll of terminal event does not duplicate bubbles", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "open vercel" }];
    const first = mergeBrowserLifecycleEvents(base, [completed], new Set());
    expect(first.added).toBe(1);
    writeSeenBrowserEventIds(first.seen);
    const second = mergeBrowserLifecycleEvents(first.messages, [completed], readSeenBrowserEventIds());
    expect(second.added).toBe(0);
    expect(second.messages).toHaveLength(2);
  });

  it("dedupes by session_id and event_type composite key", () => {
    const dup: BrowserSessionEventRecord = {
      ...completed,
      id: "different-id-should-not-matter",
    };
    const seen = new Set([`${completed.session_id}:${completed.event_type}`]);
    const merged = mergeBrowserLifecycleEvents([], [dup], seen);
    expect(merged.added).toBe(0);
    expect(browserEventDedupeKey(completed)).toBe("bsess-1:session_completed");
  });
});
