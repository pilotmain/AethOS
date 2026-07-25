import { describe, expect, it } from "vitest";

import {
  normalizeProviderSettings,
  providerCardHeadline,
  type ProviderSettingsViewModel,
} from "@/lib/settings/providerSettings";

const FULL_PAYLOAD = {
  full_reasoning: {
    status: "Not configured",
    ready: false,
    provider: "Anthropic",
    model: "claude-sonnet-4-20250514",
  },
  flags: { use_real_llm: false, anthropic_key_set: false, active_provider: "none" },
  requirements: [
    { key: "USE_REAL_LLM", value: "true", met: false, ok: false },
    { key: "ANTHROPIC_API_KEY", value: "set in .env", met: false, ok: false },
    { key: "API restart", value: "after .env changes", met: false, ok: false },
  ],
  restart_required: true,
  deterministic_note: "deterministic ok",
  template_fallback_note: "template ok",
  user_message: "not enabled",
  configured: false,
};

describe("providerSettingsCardDefensive", () => {
  it("handles undefined input without throwing", () => {
    const vm = normalizeProviderSettings(undefined);
    expect(vm.unavailable).toBe(true);
    expect(vm.statusLabel).toBe("Unknown");
    expect(() => providerCardHeadline(vm)).not.toThrow();
  });

  it("handles missing full_reasoning", () => {
    const vm = normalizeProviderSettings({ configured: false, use_real_llm: false });
    expect(vm.statusLabel).toBe("Not configured");
    expect(vm.unavailable).toBe(false);
  });

  it("handles deployment settings accidentally passed", () => {
    const vm = normalizeProviderSettings({
      response_mode: "deterministic_first",
      use_real_llm: false,
      provider_ready: false,
      model: "claude-sonnet-4-20250514",
      active_provider: "none",
    });
    expect(vm.unavailable).toBe(true);
    expect(vm.userMessage).toMatch(/Deployment settings/);
  });

  it("normalizes full provider endpoint payload", () => {
    const vm = normalizeProviderSettings(FULL_PAYLOAD);
    expect(vm.ready).toBe(false);
    expect(vm.provider).toBe("Anthropic");
    expect(vm.checklist.length).toBe(3);
    expect(vm.showTemplateNotes).toBe(true);
  });
});

export function renderSafe(vm: ProviderSettingsViewModel): string {
  return `${vm.statusLabel}:${vm.ready}`;
}
