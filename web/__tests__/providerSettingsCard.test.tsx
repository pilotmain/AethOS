import { describe, expect, it } from "vitest";

import {
  formatChecklistLine,
  normalizeProviderSettings,
  providerCardHeadline,
  providerStatusColor,
} from "@/lib/settings/providerSettings";

describe("providerSettingsCard", () => {
  it("labels ready and not configured", () => {
    const notReady = normalizeProviderSettings({
      full_reasoning: { status: "Not configured", ready: false, provider: "Anthropic", model: "m" },
      flags: { use_real_llm: false, anthropic_key_set: false, active_provider: "none" },
      requirements: [],
      configured: false,
    });
    const ready = normalizeProviderSettings({
      full_reasoning: { status: "Ready", ready: true, provider: "Anthropic", model: "m" },
      flags: { use_real_llm: true, anthropic_key_set: true, active_provider: "anthropic" },
      requirements: [],
      configured: true,
    });
    expect(providerCardHeadline(notReady)).toContain("Not configured");
    expect(providerCardHeadline(ready)).toContain("Ready");
    expect(providerStatusColor(ready)).toBe("#86efac");
  });

  it("formats checklist lines", () => {
    expect(formatChecklistLine({ label: "USE_REAL_LLM — true", ok: false })).toMatch(/^○/);
    expect(formatChecklistLine({ label: "USE_REAL_LLM — true", ok: true })).toMatch(/^✓/);
  });
});
