/** Suppress repeated probes to endpoints that returned 404. */

const unsupportedPaths = new Set<string>();

/** Legacy paths that must not be polled — clean AethOS uses runtime/settings/browser only. */
export const LEGACY_FORBIDDEN_PATHS = [
  "/api/setup-creds",
  "/api/v1/auth/ping",
  "/api/v1/setup/auth-diagnostics",
] as const;

export function extractApiPath(url: string): string {
  if (url.includes("/api/")) {
    return url.slice(url.indexOf("/api/"));
  }
  return url;
}

export function isLegacyForbiddenUrl(url: string): boolean {
  const path = extractApiPath(url);
  return LEGACY_FORBIDDEN_PATHS.some((legacy) => path.includes(legacy));
}

export function markEndpointUnsupported(path: string): void {
  unsupportedPaths.add(extractApiPath(path));
}

export function isEndpointUnsupported(path: string): boolean {
  return unsupportedPaths.has(extractApiPath(path));
}

export function assertNoLegacyProbe(path: string): void {
  if (isLegacyForbiddenUrl(path)) {
    throw new Error(`Legacy endpoint probe blocked: ${extractApiPath(path)}`);
  }
}

export async function fetchWithRouteProbe(
  url: string,
  init?: RequestInit,
): Promise<Response> {
  assertNoLegacyProbe(url);
  const path = extractApiPath(url);
  if (isEndpointUnsupported(path)) {
    return new Response(null, { status: 404, statusText: "Unsupported (cached)" });
  }
  const res = await fetch(url, init);
  if (res.status === 404) {
    markEndpointUnsupported(path);
  }
  return res;
}

