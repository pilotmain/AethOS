/** Clean API bootstrap — uses /api/v1/health only (no legacy Nexa setup probes). */
import { apiBase } from "@/lib/api";
import { assertNoLegacyProbe } from "@/lib/api/routeProbe";

export type ApiBootstrapResult = {
  ok: boolean;
  apiBase: string;
  chatReady: boolean;
  label: string;
  panel: string;
};

/** Preferred connection check for chat and Mission Control boot. */
export async function bootstrapApiConnection(): Promise<ApiBootstrapResult> {
  const base = apiBase();
  const healthUrl = `${base}/api/v1/health`;
  assertNoLegacyProbe(healthUrl);
  const res = await fetch(healthUrl, { cache: "no-store" });
  if (!res.ok) {
    return {
      ok: false,
      apiBase: base,
      chatReady: false,
      label: "API offline",
      panel: "unavailable",
    };
  }
  const body = (await res.json()) as {
    chat_ready?: boolean;
    label?: string;
    panel?: string;
  };
  return {
    ok: true,
    apiBase: base,
    chatReady: Boolean(body.chat_ready),
    label: String(body.label ?? "Connected"),
    panel: String(body.panel ?? "healthy"),
  };
}
