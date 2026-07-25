/**
 * Public URL prefix when the UI is mounted under /aethos (Railway production).
 *
 * Rule: Next `router.push/replace` and `<Link href>` already honor `basePath` in
 * next.config — use bare paths (`/`, `/login`). Raw browser nav, `<a href>`, SW,
 * manifest, and emailed links must call `withBasePath()` exactly once.
 */
export function publicBasePath(): string {
  const fromEnv = process.env.NEXT_PUBLIC_BASE_PATH;
  if (fromEnv !== undefined) return fromEnv;
  if (typeof window !== "undefined") {
    const { pathname } = window.location;
    if (pathname === "/aethos" || pathname.startsWith("/aethos/")) return "/aethos";
  }
  return "";
}

export function withBasePath(path: string): string {
  const base = publicBasePath();
  if (!path.startsWith("/")) return `${base}/${path}`;
  return base ? `${base}${path}` : path;
}

/** Canonical unauthenticated entry — always includes the deployed base path. */
export function authLoginPath(): string {
  return withBasePath("/login");
}

export function redirectToAuthLogin(): void {
  if (typeof window === "undefined") return;
  window.location.href = authLoginPath();
}
