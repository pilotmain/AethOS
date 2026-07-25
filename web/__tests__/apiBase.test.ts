import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiBase } from "@/lib/api";

describe("apiBase", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.stubGlobal("window", undefined);
    process.env = { ...originalEnv };
    delete process.env.NEXT_PUBLIC_API_BASE;
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.unstubAllGlobals();
  });

  it("uses pilotmain same-origin proxy when opened on pilotmain.com", () => {
    vi.stubGlobal("window", {
      location: { origin: "https://pilotmain.com", hostname: "pilotmain.com" },
    });
    expect(apiBase()).toBe("https://pilotmain.com/aethos-api");
  });

  it("uses same-origin proxy in dev when UI host differs from API base", () => {
    vi.stubEnv("NODE_ENV", "development");
    process.env.NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8010";
    vi.stubGlobal("window", {
      location: { origin: "http://localhost:3000", hostname: "localhost" },
    });
    expect(apiBase()).toBe("http://localhost:3000");
  });

  it("uses explicit API base when UI and API share host", () => {
    vi.stubEnv("NODE_ENV", "development");
    process.env.NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8010";
    vi.stubGlobal("window", {
      location: { origin: "http://127.0.0.1:3000", hostname: "127.0.0.1" },
    });
    expect(apiBase()).toBe("http://127.0.0.1:8010");
  });

  it("uses localhost API in development SSR when not on pilotmain", () => {
    vi.stubEnv("NODE_ENV", "development");
    expect(apiBase()).toBe("http://localhost:8010");
  });

  it("prefers NEXT_PUBLIC_API_BASE when set", () => {
    process.env.NEXT_PUBLIC_API_BASE = "https://example.test/api/";
    expect(apiBase()).toBe("https://example.test/api");
  });
});
