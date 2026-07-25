import { beforeEach, describe, expect, it, vi } from "vitest";

import { mergeLifecycleEvents } from "@/lib/chat/actionLifecycleBridge";
import {
  mergeBrowserLifecycleEvents,
  readSeenBrowserEventIds,
  writeSeenBrowserEventIds,
} from "@/lib/chat/browserLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";
import type { BrowserSessionEventRecord } from "@/lib/missionControl/browserSessions";

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

describe("browserSessionEventsDoNotReplayAfterChat", () => {
  beforeEach(() => {
    stubSessionStorage();
  });

  it("unrelated user message does not replay browser terminal events", () => {
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
    let messages: CachedMessage[] = [{ id: "1", role: "user", content: "open vercel" }];
    const first = mergeBrowserLifecycleEvents(messages, [completed], new Set());
    writeSeenBrowserEventIds(first.seen);
    messages = [
      ...first.messages,
      { id: "2", role: "user", content: "can you tell me all applications in vercel" },
      { id: "3", role: "assistant", content: "Here are common Vercel apps…" },
    ];
    const replay = mergeBrowserLifecycleEvents(messages, [completed], readSeenBrowserEventIds());
    expect(replay.added).toBe(0);
    expect(replay.messages.filter((m) => m.role === "system")).toHaveLength(1);
  });

  it("action launching/opened render once; browser poll does not add duplicates", () => {
    const base: CachedMessage[] = [
      { id: "1", role: "user", content: "open vercel.com in browser automation" },
    ];
    const actionEvents = [
      {
        id: "act-1:action_approved",
        action_id: "act-1",
        event_type: "action_approved" as const,
        message: "⏳ Browser session launching — vercel.com…",
        status: "approved",
        action_type: "browser_navigation_plan",
        session_id: "default",
        at: 1,
      },
      {
        id: "act-1:action_completed",
        action_id: "act-1",
        event_type: "action_completed" as const,
        message: "🌐 Browser session opened — vercel.com",
        status: "completed",
        action_type: "browser_navigation_plan",
        session_id: "default",
        at: 2,
      },
    ];
    const afterActions = mergeLifecycleEvents(base, actionEvents, new Set());
    expect(afterActions.messages.filter((m) => m.role === "system")).toHaveLength(2);

    const browserLaunch = {
      id: "bsess-1:session_launching",
      session_id: "bsess-1",
      event_type: "session_launching",
      message: "⏳ Browser session launching — vercel.com…",
      status: "launching",
      target: "vercel.com",
      chat_session_id: "default",
      at: 1,
    };
    const browserOpen = {
      id: "bsess-1:session_running",
      session_id: "bsess-1",
      event_type: "session_running",
      message: "🌐 Browser session opened — vercel.com",
      status: "running",
      target: "vercel.com",
      chat_session_id: "default",
      at: 2,
    };
    const afterBrowser = mergeBrowserLifecycleEvents(
      afterActions.messages,
      [browserLaunch, browserOpen],
      new Set(),
    );
    expect(afterBrowser.added).toBe(0);
    expect(afterBrowser.messages.filter((m) => m.role === "system")).toHaveLength(2);
  });
});
