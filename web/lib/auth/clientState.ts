/** Purge client stores on auth transitions — prevents cross-user data leaks on shared browsers. */

import {
  ANONYMOUS_USER_SCOPE,
  AUTH_SCOPE_MARKER_KEY,
  setActiveUserScope,
  userScopeFromSession,
} from "@/lib/auth/userScope";
import type { AuthSessionState } from "@/lib/onboarding/tenantSetup";

const LEGACY_GLOBAL_KEYS = [
  "aethos_chat_threads_v1",
  "aethos_chat_active_thread_id",
] as const;

function shouldClearKey(key: string): boolean {
  return key.startsWith("aethos_") || key.startsWith("aethos.");
}

export function clearUserScopedClientState(): void {
  if (typeof window === "undefined") return;
  for (const store of [localStorage, sessionStorage]) {
    const keys: string[] = [];
    for (let i = 0; i < store.length; i++) {
      const key = store.key(i);
      if (key && shouldClearKey(key)) keys.push(key);
    }
    keys.forEach((key) => store.removeItem(key));
  }
  for (const key of LEGACY_GLOBAL_KEYS) {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  }
  sessionStorage.removeItem("aethos_chat_messages");
  sessionStorage.removeItem("aethos_chat_session_id");
  sessionStorage.removeItem(AUTH_SCOPE_MARKER_KEY);
}

/** After login/register — always start from a clean client cache. */
export function applyAuthSessionAfterLogin(session: AuthSessionState | null): void {
  clearUserScopedClientState();
  const scope = userScopeFromSession(session);
  setActiveUserScope(scope);
  if (scope !== ANONYMOUS_USER_SCOPE) {
    sessionStorage.setItem(AUTH_SCOPE_MARKER_KEY, scope);
  }
}

/** On cold load / session refresh — clear only when the signed-in user changed. */
export function applyAuthSessionOnLoad(session: AuthSessionState | null): void {
  const scope = userScopeFromSession(session);
  const previous = sessionStorage.getItem(AUTH_SCOPE_MARKER_KEY);
  if (session?.authenticated && previous && previous !== scope) {
    clearUserScopedClientState();
  }
  setActiveUserScope(scope);
  if (session?.authenticated && scope !== ANONYMOUS_USER_SCOPE) {
    sessionStorage.setItem(AUTH_SCOPE_MARKER_KEY, scope);
  } else if (!session?.authenticated) {
    setActiveUserScope(ANONYMOUS_USER_SCOPE);
    sessionStorage.removeItem(AUTH_SCOPE_MARKER_KEY);
  }
}
