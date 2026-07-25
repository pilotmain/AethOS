import { describe, expect, it } from "vitest";

import { agentAvatar, AVATAR_STYLES } from "@/lib/missionControl/agentAvatars";

describe("agentAvatar", () => {
  it("maps known roles to distinct glyphs + colors", () => {
    expect(agentAvatar("marketing").glyph).toBe("📣");
    expect(agentAvatar("architect").glyph).toBe("🏛️");
    expect(agentAvatar("developer").glyph).toBe("💻");
    expect(agentAvatar("qa: test strategy").glyph).toBe("🧪");
    expect(agentAvatar("devops").glyph).toBe("🚀");
    expect(agentAvatar("research").glyph).toBe("🔬");
    expect(agentAvatar("writer").glyph).toBe("✍️");
    expect(agentAvatar("analyst").glyph).toBe("📊");
    expect(agentAvatar("orchestrator").glyph).toBe("🧠");
    // distinct colors per role
    expect(agentAvatar("marketing").color).not.toBe(agentAvatar("analyst").color);
  });

  it("falls back to a robot for unknown roles", () => {
    expect(agentAvatar("xyzzy").glyph).toBe("🤖");
  });

  it("derives initials", () => {
    expect(agentAvatar("marketing lead").initials).toBe("ML");
    expect(agentAvatar("qa_verification").initials).toBe("QV");
    expect(agentAvatar("architect").initials).toBe("AR");
  });

  it("offers three symbol styles", () => {
    expect(AVATAR_STYLES.map((s) => s.id)).toEqual(["emoji", "initials", "dot"]);
  });
});
