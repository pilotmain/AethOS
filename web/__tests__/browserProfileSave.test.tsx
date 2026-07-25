import { describe, expect, it } from "vitest";

import {
  formatBrowserProfileSaveError,
  parseBrowserApiError,
} from "@/lib/missionControl/browserProfileErrors";

describe("browserProfileSave", () => {
  it("formats network errors without generic Failed to fetch", () => {
    const msg = formatBrowserProfileSaveError(new TypeError("Failed to fetch"));
    expect(msg).toMatch(/could not reach AethOS API/i);
    expect(msg).not.toBe("Failed to fetch");
  });

  it("parses structured FastAPI error body", async () => {
    const res = new Response(
      JSON.stringify({
        detail: {
          ok: false,
          code: "SESSION_NOT_ACTIVE",
          detail: "Save failed — browser session expired before persistence.",
        },
      }),
      { status: 409, headers: { "Content-Type": "application/json" } },
    );
    const msg = await parseBrowserApiError(res);
    expect(msg).toMatch(/expired/i);
    expect(msg).not.toMatch(/^Failed to fetch$/i);
  });
});
