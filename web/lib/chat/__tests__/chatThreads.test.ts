import { beforeEach, describe, expect, it, vi } from "vitest";

import { setActiveUserScope } from "@/lib/auth/userScope";
import {
  createChatThread,
  getActiveSessionId,
  getActiveThread,
  listChatThreads,
  mergeServerThreadsIntoLocal,
  selectChatThread,
  updateActiveThreadMessages,
} from "@/lib/chat/chatThreads";

describe("chatThreads", () => {
  beforeEach(() => {
    setActiveUserScope("test-user@example.com");
    const store: Record<string, string> = {};
    vi.stubGlobal("window", globalThis);
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
      removeItem: (key: string) => {
        delete store[key];
      },
    });
    vi.stubGlobal("sessionStorage", {
      getItem: (key: string) => store[`ss:${key}`] ?? null,
      setItem: (key: string, value: string) => {
        store[`ss:${key}`] = value;
      },
    });
  });

  it("creates multiple threads with distinct session ids", () => {
    const a = createChatThread("First");
    const b = createChatThread("Second");
    expect(a.sessionId).not.toBe(b.sessionId);
    expect(listChatThreads().length).toBeGreaterThanOrEqual(2);
    selectChatThread(b.id);
    expect(getActiveSessionId()).toBe(b.sessionId);
  });

  it("a new window does not inherit another window's active thread", () => {
    // Window A creates and selects a thread (its active pointer → sessionStorage).
    const a = createChatThread("Window A chat");
    selectChatThread(a.id);
    expect(getActiveSessionId()).toBe(a.sessionId);

    // Simulate opening a fresh window/tab: the thread LIST (localStorage) persists,
    // but the per-tab active pointer (sessionStorage) is gone.
    vi.stubGlobal("sessionStorage", {
      getItem: () => null,
      setItem: () => {},
    });

    // The fresh window must start its OWN independent chat, not adopt A.
    const fresh = getActiveThread();
    expect(fresh.id).not.toBe(a.id);
    expect(fresh.sessionId).not.toBe(a.sessionId);
    // A is still available in the shared list to switch back to.
    expect(listChatThreads().some((t) => t.id === a.id)).toBe(true);
  });

  it("a fresh window does NOT adopt a server thread during merge (no cross-window bleed)", () => {
    // Seed a local thread so readStore() does NOT auto-migrate (which would set a
    // pointer and mask the bug). This mirrors a window that already has the shared
    // thread list in localStorage.
    createChatThread("Existing local");

    // Simulate a fresh window: the thread LIST (localStorage) persists, but the
    // per-tab active pointer (sessionStorage) is gone — and writes DO persist so a
    // buggy adoption would be observable.
    const freshSS: Record<string, string> = {};
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => freshSS[k] ?? null,
      setItem: (k: string, v: string) => {
        freshSS[k] = v;
      },
    });

    // Another window's conversation arrives from the server, unambiguously newest.
    mergeServerThreadsIntoLocal([
      {
        session_id: "sess-other-window",
        title: "Other window conversation",
        updated_at: Date.now() + 1_000_000,
        messages: [
          { id: "m1", role: "user" as const, content: "secret from the other window" },
          { id: "m2", role: "assistant" as const, content: "reply" },
        ],
      },
    ]);

    // This window must start its OWN empty chat, not the other window's content.
    const active = getActiveThread();
    expect(active.sessionId).not.toBe("sess-other-window");
    expect(active.messages).toHaveLength(0);
    // The other conversation is still in the shared list to switch to deliberately.
    expect(listChatThreads().some((t) => t.title === "Other window conversation")).toBe(true);
  });

  it("merge repairs only a STALE active pointer (points to a vanished thread)", () => {
    const a = createChatThread("Keep me");
    selectChatThread(a.id);
    // Pointer is valid → merge must leave it alone even as server rows arrive.
    mergeServerThreadsIntoLocal([
      { session_id: "sess-new", title: "Newer server thread", updated_at: Date.now() + 10000 },
    ]);
    expect(getActiveSessionId()).toBe(a.sessionId);
  });

  it("persists messages on active thread", () => {
    const thread = getActiveThread();
    updateActiveThreadMessages([
      { id: "1", role: "user", content: "compare GBrain vs wiki" },
      { id: "2", role: "assistant", content: "Done" },
    ]);
    selectChatThread(thread.id);
    const restored = getActiveThread();
    expect(restored.messages).toHaveLength(2);
    expect(restored.title).toMatch(/compare GBrain/i);
  });
});
