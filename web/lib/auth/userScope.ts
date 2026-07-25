/** Per-user browser scope id — matches server tenant_id (authenticated email). */

import type { AuthSessionState } from "@/lib/onboarding/tenantSetup";

export const ANONYMOUS_USER_SCOPE = "anonymous";

let activeScopeId: string = ANONYMOUS_USER_SCOPE;

export const AUTH_SCOPE_MARKER_KEY = "aethos_active_user_scope";

export function userScopeFromSession(session: AuthSessionState | null | undefined): string {
  if (!session?.authenticated) return ANONYMOUS_USER_SCOPE;
  const email = session.user?.email?.trim().toLowerCase();
  return email && email.includes("@") ? email : ANONYMOUS_USER_SCOPE;
}

export function getActiveUserScope(): string {
  return activeScopeId;
}

export function setActiveUserScope(scopeId: string): void {
  activeScopeId = scopeId.trim() ? scopeId.trim().toLowerCase() : ANONYMOUS_USER_SCOPE;
}

export function scopedStorageKey(base: string): string {
  return `${base}:${getActiveUserScope()}`;
}
