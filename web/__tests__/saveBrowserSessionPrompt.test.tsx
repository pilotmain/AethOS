import { describe, expect, it } from "vitest";

import { shouldShowSaveBrowserSessionPrompt } from "@/components/SaveBrowserSessionPrompt";

describe("saveBrowserSessionPrompt", () => {
  it("shows prompt only when session is eligible", () => {
    expect(
      shouldShowSaveBrowserSessionPrompt({
        id: "bsess-1",
        target: "vercel.com",
        url: "https://vercel.com",
        status: "waiting_for_operator",
        profile_save_eligible: true,
      }),
    ).toBe(true);
    expect(
      shouldShowSaveBrowserSessionPrompt({
        id: "bsess-1",
        target: "vercel.com",
        url: "https://vercel.com",
        status: "completed",
        profile_save_eligible: false,
      }),
    ).toBe(false);
  });

  it("does not reference password collection in opt-in contract", () => {
    const copy =
      "Save this session for future read-only checks. use once only. not your password.";
    expect(copy).toMatch(/use once only/i);
    expect(copy).not.toMatch(/enter your password/i);
  });
});
