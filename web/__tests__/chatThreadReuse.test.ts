import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  getActiveThreadId,
  listChatThreads,
  updateThreadMessages,
} from "@/lib/chat/chatThreads";

/** Separate local vs session stores so we can simulate a fresh tab/login (which
 * starts with empty sessionStorage but keeps the localStorage thread list). */
function mockSplitStorage() {
  const local: Record<string, string> = {};
  const session: Record<string, string> = {};
  const mk = (s: Record<string, string>) => ({
    getItem: (k: string) => s[k] ?? null,
    setItem: (k: string, v: string) => void (s[k] = v),
    removeItem: (k: string) => void delete s[k],
    clear: () => Object.keys(s).forEach((k) => delete s[k]),
    key: (i: number) => Object.keys(s)[i] ?? null,
    get length() {
      return Object.keys(s).length;
    },
  });
  vi.stubGlobal("localStorage", mk(local));
  vi.stubGlobal("sessionStorage", mk(session));
  return { session };
}

describe("chat thread reuse on fresh tab/login", () => {
  let session: Record<string, string>;
  beforeEach(() => {
    vi.stubGlobal("window", globalThis);
    ({ session } = mockSplitStorage());
  });

  function freshTab() {
    // A new window/login has its own (empty) sessionStorage — drop the per-tab pointer.
    Object.keys(session).forEach((k) => delete session[k]);
  }

  it("reuses an existing empty 'New chat' instead of piling up duplicates", () => {
    const first = getActiveThreadId();
    expect(listChatThreads()).toHaveLength(1);

    freshTab();
    const second = getActiveThreadId();
    freshTab();
    const third = getActiveThreadId();

    // No new empties created — the same empty thread is adopted each time.
    expect(listChatThreads()).toHaveLength(1);
    expect(second).toBe(first);
    expect(third).toBe(first);
  });

  it("does NOT adopt a thread that already has a conversation (starts a fresh one)", () => {
    const first = getActiveThreadId();
    updateThreadMessages(first, [{ role: "user", content: "hello" } as never]);

    freshTab();
    const second = getActiveThreadId();

    expect(second).not.toBe(first); // the conversation thread is not hijacked
    expect(listChatThreads()).toHaveLength(2); // a fresh empty one was created
  });
});
