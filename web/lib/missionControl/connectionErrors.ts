/** Structured connection save errors — never raw Failed to fetch. */

import { apiBase } from "@/lib/api";

export type ConnectionSaveDebug = {
  requestUrl: string;
  httpStatus?: number;
  errorCode?: string;
  apiBase: string;
};

export function parseConnectionErrorPayload(message: string): {
  code?: string;
  detail?: string;
} {
  const trimmed = (message || "").trim();
  if (!trimmed) return {};
  try {
    const parsed = JSON.parse(trimmed) as { code?: string; detail?: string; ok?: boolean };
    if (parsed && typeof parsed === "object") {
      return { code: parsed.code, detail: parsed.detail || trimmed };
    }
  } catch {
    // FastAPI may return {"detail":"..."} or plain text
  }
  if (trimmed.startsWith("{")) return { detail: trimmed };
  return { detail: trimmed };
}

export function formatConnectionSaveError(
  err: unknown,
  debug?: Partial<ConnectionSaveDebug>,
): { message: string; debug?: ConnectionSaveDebug } {
  const base = apiBase();
  const requestUrl = debug?.requestUrl ?? `${base}/api/v1/connections/vercel/credentials`;

  if (err instanceof TypeError && /failed to fetch/i.test(err.message)) {
    return {
      message:
        "Could not reach AethOS API while saving token. Check that the API is running and reachable " +
        `at ${base}.`,
      debug: {
        requestUrl,
        apiBase: base,
        errorCode: "NETWORK_ERROR",
        ...debug,
      },
    };
  }

  const raw = err instanceof Error ? err.message : String(err);
  const parsed = parseConnectionErrorPayload(raw);
  const code = parsed.code || debug?.errorCode;
  const detail = parsed.detail || raw;
  const httpStatus = debug?.httpStatus;

  if (
    httpStatus === 401 ||
    code === "authentication_required" ||
    /authentication_required/i.test(raw)
  ) {
    return {
      message:
        "Not signed in to the API (session cookie missing). Use http://localhost:3000 for the UI " +
        "(not 127.0.0.1) so login cookies reach the API, then sign in again.",
      debug: { requestUrl, apiBase: base, httpStatus: 401, errorCode: "authentication_required" },
    };
  }

  if (code === "CREDENTIAL_VAULT_UNAVAILABLE") {
    return {
      message: "Token save failed: credential vault dependency missing (`cryptography`).",
      debug: { requestUrl, apiBase: base, httpStatus: debug?.httpStatus, errorCode: code },
    };
  }
  if (code === "INVALID_CREDENTIAL_PAYLOAD") {
    return {
      message: `Token save failed: ${detail}`,
      debug: { requestUrl, apiBase: base, httpStatus: debug?.httpStatus, errorCode: code },
    };
  }
  if (code) {
    return {
      message: `Token save failed: ${detail}`,
      debug: { requestUrl, apiBase: base, httpStatus: debug?.httpStatus, errorCode: code },
    };
  }
  if (/failed to fetch/i.test(raw)) {
    return {
      message: `Could not reach AethOS API while saving token. API base: ${base}.`,
      debug: { requestUrl, apiBase: base, errorCode: "NETWORK_ERROR" },
    };
  }
  return {
    message: detail ? `Token save failed: ${detail}` : "Token save failed.",
    debug: { requestUrl, apiBase: base, httpStatus: debug?.httpStatus, errorCode: code },
  };
}

export function isDevConnectionsDebug(): boolean {
  return process.env.NODE_ENV === "development";
}
