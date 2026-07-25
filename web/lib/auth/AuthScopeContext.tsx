"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  applyAuthSessionAfterLogin,
  applyAuthSessionOnLoad,
  clearUserScopedClientState,
} from "@/lib/auth/clientState";
import { ANONYMOUS_USER_SCOPE, getActiveUserScope, setActiveUserScope } from "@/lib/auth/userScope";
import { apiBase } from "@/lib/api";
import { redirectToAuthLogin } from "@/lib/pwa/basePath";
import {
  fetchAuthSession,
  type AuthSessionState,
} from "@/lib/onboarding/tenantSetup";

type AuthScopeContextValue = {
  scope: string;
  session: AuthSessionState | null;
  email: string | undefined;
  authenticated: boolean;
  authEnabled: boolean;
  refreshSession: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthScopeContext = createContext<AuthScopeContextValue | null>(null);

export function useAuthScope(): AuthScopeContextValue {
  const ctx = useContext(AuthScopeContext);
  if (!ctx) {
    return {
      scope: ANONYMOUS_USER_SCOPE,
      session: null,
      email: undefined,
      authenticated: false,
      authEnabled: false,
      refreshSession: async () => {},
      logout: async () => {},
    };
  }
  return ctx;
}

export function AuthScopeProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSessionState | null>(null);
  const [scope, setScope] = useState(getActiveUserScope());

  const refreshSession = useCallback(async () => {
    const next = await fetchAuthSession();
    if (!next?.authenticated && session?.authenticated) {
      clearUserScopedClientState();
      setActiveUserScope(ANONYMOUS_USER_SCOPE);
      setSession(next);
      setScope(ANONYMOUS_USER_SCOPE);
      redirectToAuthLogin();
      return;
    }
    applyAuthSessionOnLoad(next);
    setSession(next);
    setScope(getActiveUserScope());
  }, [session?.authenticated]);

  useEffect(() => {
    const isPublicEntry = () => {
      const path = window.location.pathname.replace(/\/$/, "") || "/";
      return path === "/login" || path.endsWith("/login") || path.endsWith("/verify-email");
    };

    void refreshSession();
    if (isPublicEntry()) return;

    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible" && !isPublicEntry()) void refreshSession();
    }, 60_000);
    return () => window.clearInterval(interval);
  }, [refreshSession]);

  const logout = useCallback(async () => {
    try {
      await fetch(`${apiBase()}/api/v1/aethos-identity/logout`, {
        method: "POST",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
    } catch {
      /* best-effort */
    }
    clearUserScopedClientState();
    setActiveUserScope(ANONYMOUS_USER_SCOPE);
    setSession(null);
    setScope(ANONYMOUS_USER_SCOPE);
    redirectToAuthLogin();
  }, []);

  const value = useMemo<AuthScopeContextValue>(
    () => ({
      scope,
      session,
      email: session?.user?.email,
      authenticated: Boolean(session?.authenticated),
      authEnabled: Boolean(session?.auth_enabled),
      refreshSession,
      logout,
    }),
    [scope, session, refreshSession, logout],
  );

  return <AuthScopeContext.Provider value={value}>{children}</AuthScopeContext.Provider>;
}

export async function completeLoginClientState(): Promise<AuthSessionState | null> {
  const session = await fetchAuthSession();
  applyAuthSessionAfterLogin(session);
  return session;
}
