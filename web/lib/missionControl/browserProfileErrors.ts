/** Parse browser profile API errors — never show generic "Failed to fetch". */

export type BrowserProfileErrorBody = {
  ok?: boolean;
  code?: string;
  detail?: string;
};

export function formatBrowserProfileSaveError(err: unknown, status?: number): string {
  if (err instanceof TypeError && /fetch/i.test(err.message)) {
    const base = typeof window !== "undefined" ? "(check API is running)" : "";
    return `Save failed — could not reach AethOS API ${base}`.trim();
  }
  if (err instanceof Error) {
    const msg = err.message.trim();
    if (msg && !/^failed to fetch$/i.test(msg)) {
      return msg.startsWith("Save failed") ? msg : `Save failed — ${msg}`;
    }
  }
  if (status === 404) {
    return "Save failed — browser session not found (404).";
  }
  if (status === 409) {
    return "Save failed — browser session expired or not active (409).";
  }
  if (status === 422) {
    return "Save failed — unable to persist Playwright state (422).";
  }
  if (status === 504) {
    return "Save failed — operation timed out (504).";
  }
  return "Save failed — unexpected error. Check API logs.";
}

export async function parseBrowserApiError(res: Response): Promise<string> {
  try {
    const raw = (await res.json()) as { detail?: string | BrowserProfileErrorBody };
    const payload = raw.detail;
    if (typeof payload === "string" && payload) {
      return payload.startsWith("Save failed") ? payload : `Save failed — ${payload}`;
    }
    if (payload && typeof payload === "object" && typeof payload.detail === "string") {
      return payload.detail;
    }
    if (payload && typeof payload === "object" && typeof payload.code === "string") {
      return `Save failed — ${payload.code}`;
    }
  } catch {
    /* ignore */
  }
  return formatBrowserProfileSaveError(new Error(""), res.status);
}
