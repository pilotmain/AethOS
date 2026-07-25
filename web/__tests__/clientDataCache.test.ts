import { beforeEach, describe, expect, it, vi } from "vitest";

import { readCached, swrFetch, writeCached } from "@/lib/clientDataCache";

describe("clientDataCache", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
    });
  });

  it("returns cached data immediately and revalidates", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true });
    const first = await swrFetch("probe-swr", fetcher);
    expect(first).toEqual({ ok: true });
    const second = await swrFetch("probe-swr", fetcher);
    expect(second).toEqual({ ok: true });
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(readCached("probe-swr")).toEqual({ ok: true });
  });
});
