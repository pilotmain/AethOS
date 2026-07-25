import { describe, expect, it } from "vitest";

import { formatConnectionSaveError } from "@/lib/missionControl/connectionErrors";

describe("connectionsTokenSaveError", () => {
  it("does not render raw Failed to fetch", () => {
    const out = formatConnectionSaveError(new TypeError("Failed to fetch"));
    expect(out.message).not.toMatch(/^Failed to fetch$/i);
    expect(out.message).toMatch(/Could not reach AethOS API/i);
  });

  it("renders structured vault dependency errors", () => {
    const err = new Error("Credential vault dependency missing");
    (err as Error & { code?: string }).code = "CREDENTIAL_VAULT_UNAVAILABLE";
    const out = formatConnectionSaveError(err, { httpStatus: 503, errorCode: "CREDENTIAL_VAULT_UNAVAILABLE" });
    expect(out.message).toMatch(/cryptography/i);
  });
});
