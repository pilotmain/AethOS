import { apiBase } from "@/lib/api";

export type PwaStatus = {
  ok: boolean;
  pwa_installable: boolean;
  offline_shell: boolean;
  web_push_enabled: boolean;
  vapid_public_key?: string;
  push_configured?: boolean;
  subscriptions?: number;
};

export async function fetchPwaStatus(): Promise<PwaStatus | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/pwa/status`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as PwaStatus;
  } catch {
    return null;
  }
}

export async function subscribeWebPush(subscription: PushSubscription): Promise<boolean> {
  const json = subscription.toJSON();
  if (!json.endpoint || !json.keys) return false;
  const res = await fetch(`${apiBase()}/api/v1/pwa/push/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      endpoint: json.endpoint,
      keys: json.keys,
      expiration_time: json.expirationTime ?? null,
      user_agent: typeof navigator !== "undefined" ? navigator.userAgent : "",
    }),
  });
  return res.ok;
}

export async function unsubscribeWebPush(endpoint: string): Promise<void> {
  await fetch(`${apiBase()}/api/v1/pwa/push/unsubscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint }),
  });
}
