/** Multi-tenant BYOK onboarding API (Phase 6). */

import { apiBase } from "@/lib/api";

export type TenantOnboardingStep = {
  id: string;
  title: string;
  hint?: string;
  completed: boolean;
  status: string;
};

export type TenantOnboardingState = {
  ok: boolean;
  enabled: boolean;
  required: boolean;
  complete: boolean;
  tenant_id?: string;
  steps?: TenantOnboardingStep[];
  progress?: number;
  next_step?: TenantOnboardingStep | null;
};

export type AuthSessionState = {
  authenticated: boolean;
  auth_enabled: boolean;
  self_signup_enabled: boolean;
  multi_tenant_enabled: boolean;
  is_platform_owner?: boolean;
  email_verification_required?: boolean;
  email_verified?: boolean;
  user?: {
    email: string;
    name?: string;
    roles: string[];
    permissions?: string[];
    email_verified?: boolean;
    status?: string;
    plan?: string;
    access_expires_at?: number | null;
  };
};

const creds: RequestInit = { credentials: "include" };

export async function fetchAuthSession(): Promise<AuthSessionState | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/aethos-identity/session`, creds);
    if (!res.ok) return null;
    return (await res.json()) as AuthSessionState;
  } catch {
    return null;
  }
}

export async function fetchTenantOnboarding(): Promise<TenantOnboardingState | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/tenancy/onboarding`, creds);
    if (!res.ok) return null;
    return (await res.json()) as TenantOnboardingState;
  } catch {
    return null;
  }
}

export async function completeTenantOnboarding(): Promise<TenantOnboardingState | null> {
  const res = await fetch(`${apiBase()}/api/v1/tenancy/onboarding/complete`, {
    ...creds,
    method: "POST",
  });
  if (!res.ok) return null;
  return (await res.json()) as TenantOnboardingState;
}

export async function loginWithPassword(
  email: string,
  password: string,
): Promise<{ ok: boolean; error?: string; detail?: string; verification_required?: boolean }> {
  const res = await fetch(`${apiBase()}/api/v1/aethos-identity/login`, {
    ...creds,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = (await res.json()) as { ok?: boolean; error?: string; detail?: string };
  return { ok: Boolean(data.ok), error: data.error, detail: data.detail };
}

export async function registerAccount(
  email: string,
  password: string,
  name?: string,
): Promise<{
  ok: boolean;
  error?: string;
  verification_required?: boolean;
  detail?: string;
  hint?: string;
  provider?: string;
  status?: number;
}> {
  const res = await fetch(`${apiBase()}/api/v1/aethos-identity/register`, {
    ...creds,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name: name || "" }),
  });
  const data = (await res.json()) as {
    ok?: boolean;
    error?: string;
    detail?: string;
    hint?: string;
    provider?: string;
    status?: number;
    verification_required?: boolean;
  };
  return {
    ok: Boolean(data.ok),
    error: data.error,
    detail: data.detail,
    hint: data.hint,
    provider: data.provider,
    status: data.status,
    verification_required: Boolean(data.verification_required),
  };
}

export async function verifyEmailToken(token: string): Promise<{ ok: boolean; error?: string }> {
  const res = await fetch(
    `${apiBase()}/api/v1/aethos-identity/verify-email?token=${encodeURIComponent(token)}`,
    creds,
  );
  const data = (await res.json()) as { ok?: boolean; error?: string };
  return { ok: Boolean(data.ok), error: data.error };
}

export async function resendVerificationEmail(
  email: string,
): Promise<{ ok: boolean; error?: string; detail?: string; hint?: string; provider?: string; status?: number }> {
  const res = await fetch(`${apiBase()}/api/v1/aethos-identity/resend-verification`, {
    ...creds,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const data = (await res.json()) as {
    ok?: boolean;
    error?: string;
    detail?: string;
    hint?: string;
    provider?: string;
    status?: number;
  };
  return {
    ok: Boolean(data.ok),
    error: data.error,
    detail: data.detail,
    hint: data.hint,
    provider: data.provider,
    status: data.status,
  };
}

export async function setRuntimeFlag(key: string, value: boolean): Promise<boolean> {
  const res = await fetch(`${apiBase()}/api/v1/config/${encodeURIComponent(key)}`, {
    ...creds,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  });
  return res.ok;
}
