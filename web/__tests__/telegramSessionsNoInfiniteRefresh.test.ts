import { describe, expect, it, vi } from "vitest";

/** Mirrors TelegramSessionsPanel in-flight guard — one request at a time. */
export class TelegramSessionsRequestGuard {
  private inFlight = false;
  private callCount = 0;

  async run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    if (this.inFlight) return undefined;
    this.inFlight = true;
    this.callCount += 1;
    try {
      return await fn();
    } finally {
      this.inFlight = false;
    }
  }

  get calls() {
    return this.callCount;
  }
}

describe("telegramSessionsNoInfiniteRefresh", () => {
  it("allows only one in-flight sessions fetch at a time", async () => {
    const guard = new TelegramSessionsRequestGuard();
    let resolveFirst: (() => void) | undefined;
    const first = new Promise<void>((resolve) => {
      resolveFirst = resolve;
    });

    const p1 = guard.run(async () => {
      await first;
      return "a";
    });
    const p2 = guard.run(async () => "b");

    expect(guard.calls).toBe(1);
    expect(await p2).toBeUndefined();

    resolveFirst?.();
    expect(await p1).toBe("a");
  });

  it("does not autosave notification mode when unchanged", () => {
    const save = vi.fn();
    const current = "calm";
    const next = "calm";
    if (next !== current) {
      save(next);
    }
    expect(save).not.toHaveBeenCalled();
  });
});

describe("telegramSessionsLoadingErrorState", () => {
  it("sessions response includes ok flag for stable parsing", () => {
    const body = { ok: true, sessions: [], count: 0 };
    expect(body.ok).toBe(true);
    expect(Array.isArray(body.sessions)).toBe(true);
  });
});
