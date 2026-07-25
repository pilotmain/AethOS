import { describe, expect, it, vi } from "vitest";

import { mcFailureAffectsChat } from "@/lib/missionControl/panelError";
import { normalizeProviderSettings } from "@/lib/settings/providerSettings";
import { readCachedMessages, writeCachedMessages } from "@/lib/chat/lanes";

describe("missionControlSettingsNoCrash", () => {
  it("never throws when normalizing bad provider payloads", () => {
    const cases: unknown[] = [undefined, null, {}, { response_mode: "x" }, { configured: true }];
    for (const input of cases) {
      expect(() => normalizeProviderSettings(input)).not.toThrow();
    }
  });

  it("MC failure does not affect chat", () => {
    expect(mcFailureAffectsChat("Provider readiness is unavailable")).toBe(false);
  });

  it("chat history survives settings navigation (session cache)", () => {
    const store: Record<string, string> = {};
    vi.stubGlobal("window", globalThis);
    const storage = {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
    };
    vi.stubGlobal("sessionStorage", storage);
    vi.stubGlobal("localStorage", storage);

    writeCachedMessages([{ id: "a", role: "user", content: "hi" }]);
    expect(readCachedMessages()).toHaveLength(1);

    const vm = normalizeProviderSettings(undefined);
    expect(vm.userMessage).toMatch(/Chat still works/i);
  });
});
