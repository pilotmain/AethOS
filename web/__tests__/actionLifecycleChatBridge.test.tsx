import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  extractActionId,
  mergeLifecycleEvents,
  pruneSeenToDisplayed,
  readTrackedActionIds,
  registerProposedActionFromMeta,
  trackActionId,
} from "@/lib/chat/actionLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("actionLifecycleChatBridge", () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal("window", globalThis);
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
    });
  });

  it("tracks proposed action from meta", () => {
    registerProposedActionFromMeta({ proposed_action_id: "act-abc123" }, "");
    expect(readTrackedActionIds()).toContain("act-abc123");
  });

  it("tracks proposed action from structured action field", () => {
    registerProposedActionFromMeta(
      { action: { id: "act-struct01", type: "vercel_cli_probe" } },
      "",
    );
    expect(readTrackedActionIds()).toContain("act-struct01");
  });

  it("pruneSeenToDisplayed drops stale seen without bubbles", () => {
    const messages: CachedMessage[] = [{ id: "1", role: "user", content: "hi" }];
    const pruned = pruneSeenToDisplayed(messages, new Set(["ghost-id"]));
    expect(pruned.size).toBe(0);
  });

  it("extracts action id from reply", () => {
    expect(extractActionId("Action proposed: `act-deadbeef`")).toBe("act-deadbeef");
  });

  it("appends lifecycle bubble once", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "hi" }];
    const events = [
      {
        id: "act-1:action_approved",
        action_id: "act-1",
        event_type: "action_approved" as const,
        message: "⏳ Action approved — running Vercel CLI probe…",
        status: "approved",
        action_type: "vercel_cli_probe",
        session_id: "default",
        at: 1,
      },
      {
        id: "act-1:action_completed",
        action_id: "act-1",
        event_type: "action_completed" as const,
        message: "✅ Vercel CLI detected — version 50.0.0",
        status: "completed",
        action_type: "vercel_cli_probe",
        session_id: "default",
        at: 2,
      },
    ];
    const seen = new Set<string>();
    const first = mergeLifecycleEvents(base, events, seen);
    expect(first.messages).toHaveLength(3);
    expect(first.messages[1]?.role).toBe("system");
    const second = mergeLifecycleEvents(first.messages, events, first.seen);
    expect(second.messages).toHaveLength(3);
  });

  it("failed action shows failure bubble", () => {
    const { messages } = mergeLifecycleEvents(
      [],
      [
        {
          id: "act-2:action_failed",
          action_id: "act-2",
          event_type: "action_failed",
          message: "⚠️ Terminal probe could not run because host executor is disabled.",
          status: "failed",
          action_type: "terminal_probe",
          session_id: "default",
          at: 1,
        },
      ],
      new Set(),
    );
    expect(messages[0]?.content).toMatch(/⚠️/);
  });

  it("trackActionId dedupes", () => {
    trackActionId("act-x");
    trackActionId("act-x");
    expect(readTrackedActionIds().filter((id) => id === "act-x")).toHaveLength(1);
  });
});
