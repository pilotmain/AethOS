import { describe, expect, it } from "vitest";

import { modelPickerLabel } from "@/lib/chat/modelSelection";

describe("modelSelection", () => {
  it("formats catalog labels with fallback", () => {
    expect(modelPickerLabel(undefined)).toBe("Default (.env)");
    expect(
      modelPickerLabel({
        id: "anthropic:claude-opus-4-6",
        provider: "anthropic",
        model: "claude-opus-4-6",
        label: "Claude Opus 4.6",
        configured: true,
      }),
    ).toBe("Claude Opus 4.6");
  });
});
