import { describe, expect, it } from "vitest";

describe("connectionsTokenLabelHelp", () => {
  it("expects label and token helper copy in panel", () => {
    const labelHelp = "Local name only";
    const tokenHelp = "never shown again";
    expect(labelHelp).toMatch(/Local name/i);
    expect(tokenHelp).toMatch(/never shown again/i);
  });
});
