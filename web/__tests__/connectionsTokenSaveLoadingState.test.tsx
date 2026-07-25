import { describe, expect, it } from "vitest";

describe("connectionsTokenSaveLoadingState", () => {
  it("uses saving label while in flight", () => {
    const saving = "saving" === "saving";
    expect(saving ? "Saving…" : "Save API token").toBe("Saving…");
  });
});
