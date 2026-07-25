/** Saved browser profiles — opt-in session persistence (no credentials in UI). */

import { apiBase } from "@/lib/api";
import { formatBrowserProfileSaveError, parseBrowserApiError } from "@/lib/missionControl/browserProfileErrors";
import { mcFetch } from "@/lib/missionControl/fetch";

export type BrowserProfileRecord = {
  profile_id: string;
  site: string;
  scope: string;
  storage_path: string;
  created_at: number;
  last_used_at?: number | null;
  user_approved_persistence: boolean;
  status: string;
  read_only_allowed: boolean;
  write_actions_allowed: boolean;
  source_session_id?: string | null;
  session_type?: string;
  expires_at?: number | null;
  expires_label?: string;
};

export type BrowserProfilesResponse = {
  profiles: BrowserProfileRecord[];
  count: number;
  active_count: number;
  profile_store_path?: string;
  store_diagnostics?: {
    profile_store_path: string;
    profile_count: number;
  };
};

export type PersistenceMode = "use_once" | "persistent" | "expires_7d" | "expires_30d";

export type SaveBrowserProfileResponse = {
  ok: boolean;
  profile: BrowserProfileRecord;
  saved: boolean;
  profile_store_path?: string;
  profile_count?: number;
};

export const fetchBrowserProfiles = () =>
  mcFetch<BrowserProfilesResponse>("/api/v1/browser/profiles");

export const saveBrowserProfile = async (
  sessionId: string,
  persistenceMode: PersistenceMode = "use_once",
): Promise<SaveBrowserProfileResponse> => {
  const sid = sessionId?.trim();
  if (!sid) {
    throw new Error(formatBrowserProfileSaveError(new Error("missing session id")));
  }
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  let res: Response;
  try {
    res = await fetch(`${apiBase()}/api/v1/browser/profiles/save`, {
      method: "POST",
      cache: "no-store",
      headers,
      body: JSON.stringify({ session_id: sid, persistence_mode: persistenceMode }),
    });
  } catch (err) {
    throw new Error(formatBrowserProfileSaveError(err));
  }
  if (!res.ok) {
    throw new Error(await parseBrowserApiError(res));
  }
  return res.json() as Promise<SaveBrowserProfileResponse>;
};

export const forgetBrowserProfile = (profileId: string) =>
  mcFetch<{ forgotten: boolean; profile_id: string }>(
    `/api/v1/browser/profiles/${encodeURIComponent(profileId)}/forget`,
    { method: "POST" },
  );

export const testBrowserProfile = (profileId: string) =>
  mcFetch<{ result: { ok: boolean; message: string; status: string } }>(
    `/api/v1/browser/profiles/${encodeURIComponent(profileId)}/test`,
    { method: "POST" },
  );
