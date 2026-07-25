/** Platform owner console — env-computed owner only (OWN_PLATFORM). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type OwnerUserRow = {
  user_id: string;
  email: string;
  name?: string;
  status?: string;
  plan?: string;
  access_expires_at?: number | null;
  entitlement_source?: string;
  roles?: string[];
  disabled?: boolean;
  last_login?: number | null;
  session_count?: number;
};

const creds: RequestInit = { credentials: "include" };

export async function fetchOwnerUsers(): Promise<{ ok: boolean; error?: string; users: OwnerUserRow[] }> {
  return mcFetch("/api/v1/aethos-identity/admin/users", creds);
}

export async function grantOwnerUser(
  userRef: string,
  body: { status?: string; plan?: string; trial_days?: number; access_expires_at?: number | null },
) {
  return mcFetch<{ ok: boolean; error?: string }>(
    `/api/v1/aethos-identity/admin/users/${encodeURIComponent(userRef)}/grant`,
    { ...creds, method: "POST", body: JSON.stringify(body) },
  );
}

export async function revokeOwnerUser(userRef: string) {
  return mcFetch<{ ok: boolean; error?: string }>(
    `/api/v1/aethos-identity/admin/users/${encodeURIComponent(userRef)}/revoke`,
    { ...creds, method: "POST", body: "{}" },
  );
}

export async function extendOwnerUser(userRef: string, days: number) {
  return mcFetch<{ ok: boolean; error?: string }>(
    `/api/v1/aethos-identity/admin/users/${encodeURIComponent(userRef)}/extend`,
    { ...creds, method: "POST", body: JSON.stringify({ days }) },
  );
}

export async function reinstateOwnerUser(userRef: string) {
  return mcFetch<{ ok: boolean; error?: string }>(
    `/api/v1/aethos-identity/admin/users/${encodeURIComponent(userRef)}/reinstate`,
    { ...creds, method: "POST", body: "{}" },
  );
}
