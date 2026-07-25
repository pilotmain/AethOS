import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  CHAT_PINNED_BOTTOM_KEY,
  isNearBottom,
  readPinnedToBottom,
  shouldAutoScroll,
  shouldShowJumpToLatest,
  writePinnedToBottom,
} from "@/lib/chat/autoScroll";

function mockScrollEl(scrollTop: number, scrollHeight: number, clientHeight: number): HTMLElement {
  return {
    scrollTop,
    scrollHeight,
    clientHeight,
  } as HTMLElement;
}

describe("chatAutoScroll", () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal("window", globalThis);
    vi.stubGlobal("sessionStorage", {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
    });
  });

  it("isNearBottom when within threshold", () => {
    const el = mockScrollEl(880, 1000, 100);
    expect(isNearBottom(el)).toBe(true);
    const far = mockScrollEl(0, 1000, 100);
    expect(isNearBottom(far)).toBe(false);
  });

  it("shouldAutoScroll when at bottom and not away", () => {
    const el = mockScrollEl(900, 1000, 100);
    expect(shouldAutoScroll(el, false)).toBe(true);
    expect(shouldAutoScroll(el, true)).toBe(false);
    expect(shouldAutoScroll(null, false)).toBe(true);
  });

  it("shouldShowJumpToLatest when away and new messages", () => {
    const el = mockScrollEl(0, 1000, 100);
    expect(shouldShowJumpToLatest(el, true, true)).toBe(true);
    expect(shouldShowJumpToLatest(el, false, false)).toBe(false);
    expect(shouldShowJumpToLatest(el, false, true)).toBe(true);
  });

  it("persists pinned-to-bottom across navigation", () => {
    writePinnedToBottom(true);
    expect(readPinnedToBottom()).toBe(true);
    writePinnedToBottom(false);
    expect(sessionStorage.getItem(CHAT_PINNED_BOTTOM_KEY)).toBe("0");
    expect(readPinnedToBottom()).toBe(false);
  });
});
