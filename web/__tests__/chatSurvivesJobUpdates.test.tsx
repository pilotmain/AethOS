import { describe, expect, it } from "vitest";

import { formatChatError } from "@/lib/chat/lanes";
import { mcFailureAffectsChat } from "@/lib/missionControl/panelError";

describe("chatSurvivesJobUpdates", () => {
  it("job API errors do not degrade chat send semantics", () => {
    expect(mcFailureAffectsChat("Jobs request failed: 503")).toBe(false);
  });

  it("formatChatError does not mention mission control panels", () => {
    const msg = formatChatError("Jobs request failed: 500");
    expect(msg).not.toMatch(/mission control/i);
  });
});
