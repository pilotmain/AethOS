import { apiBase } from "@/lib/api";

export const CLIENT_APP_VERSION =
  process.env.NEXT_PUBLIC_APP_VERSION?.trim() || "dev";

export type ServerVersionInfo = {
  version: string;
  min_supported: string;
};

export async function fetchServerVersion(): Promise<ServerVersionInfo | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/version`, { credentials: "include" });
    if (!res.ok) return null;
    return (await res.json()) as ServerVersionInfo;
  } catch {
    return null;
  }
}

/** Semver-style compare for dotted numeric releases (1.2.3). */
export function compareSemverVersions(a: string, b: string): number {
  const pa = a.split(/[.-]/).map((part) => parseInt(part, 10) || 0);
  const pb = b.split(/[.-]/).map((part) => parseInt(part, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i += 1) {
    const da = pa[i] ?? 0;
    const db = pb[i] ?? 0;
    if (da !== db) return da < db ? -1 : 1;
  }
  return 0;
}

function looksLikeSemver(value: string): boolean {
  return /^\d+(\.\d+){0,3}$/.test(value.trim());
}

export function isClientBelowMinSupported(client: string, minSupported: string): boolean {
  const min = (minSupported || "").trim();
  if (!min) return false;
  const c = (client || "").trim();
  if (!c || c === "dev") return false;
  if (looksLikeSemver(min) && looksLikeSemver(c)) {
    return compareSemverVersions(c, min) < 0;
  }
  // Git SHAs and other opaque ids — exact match only (no numeric parse traps).
  return c !== min;
}

/** Soft reload prompt when server shipped a different build than this bundle. */
export function shouldPromptVersionReload(client: string, server: string): boolean {
  const c = (client || "").trim();
  const s = (server || "").trim();
  if (!s || !c || c === "dev") return false;
  if (c === s) return false;
  return true;
}
