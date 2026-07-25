import { describe, expect, it } from "vitest";

import { pickDefaultVoiceURI, prepareSpokenText } from "@/lib/voice/speechSynthesis";

describe("prepareSpokenText", () => {
  it("omits fenced code blocks from spoken output", () => {
    const spoken = prepareSpokenText("Plan:\n```bash\nrm -rf /\n```\nDone.");
    expect(spoken).not.toContain("rm -rf");
    expect(spoken).toContain("(code block omitted)");
  });

  it("returns empty for blank input", () => {
    expect(prepareSpokenText("")).toBe("");
  });

  it("does not read horizontal rules aloud", () => {
    const spoken = prepareSpokenText("Summary\n\n---\n\nNext steps");
    expect(spoken).not.toContain("---");
    expect(spoken).not.toMatch(/-\s*-\s*-/);
    expect(spoken).toContain("Summary");
    expect(spoken).toContain("Next steps");
  });

  it("softens tables and strips emoji", () => {
    const spoken = prepareSpokenText("🗂 Status\n\n| Model | Use |\n| --- | --- |\n| Qwen | chat |");
    expect(spoken).not.toContain("|");
    expect(spoken).not.toContain("🗂");
    expect(spoken).not.toMatch(/---/);
    expect(spoken).toContain("Model");
    expect(spoken).toContain("Qwen");
  });
});

describe("pickDefaultVoiceURI", () => {
  it("prefers a Google English voice over the OS default", () => {
    const voices = [
      { voiceURI: "os", name: "Albert", lang: "en-US" },
      { voiceURI: "g", name: "Google UK English Male", lang: "en-GB" },
    ];
    expect(pickDefaultVoiceURI(voices)).toBe("g");
  });

  it("returns empty when no voices available", () => {
    expect(pickDefaultVoiceURI([])).toBe("");
  });
});
