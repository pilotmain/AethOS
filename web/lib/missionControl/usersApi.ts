/** §7 RBAC — users & roles administration (Mission Control). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AethosRole = "admin" | "approver" | "operator" | "read_only";

export type AethosUser = {
  email: string;
  name?: string;
  roles: AethosRole[];
  auth?: string;
  disabled?: boolean;
  mfa_enrolled?: boolean;
  last_login?: number | null;
};

export type UsersListResponse = {
  ok: boolean;
  error?: string;
  users: AethosUser[];
  valid_roles: AethosRole[];
};

export type SessionResponse = {
  auth_enabled: boolean;
  sso_enabled: boolean;
  mfa_enabled: boolean;
  authenticated: boolean;
  is_platform_owner?: boolean;
  user?: {
    email: string;
    name?: string;
    roles: AethosRole[];
    permissions: string[];
    mfa_enrolled: boolean;
    status?: string;
    plan?: string;
    access_expires_at?: number | null;
  };
};

const creds: RequestInit = { credentials: "include" };

export const fetchSession = () =>
  mcFetch<SessionResponse>("/api/v1/aethos-identity/session", creds);

export const fetchUsers = () =>
  mcFetch<UsersListResponse>("/api/v1/aethos-identity/users", creds);

export const setUserRoles = (email: string, roles: AethosRole[]) =>
  mcFetch<{ ok: boolean; error?: string; email?: string; roles?: AethosRole[] }>(
    "/api/v1/aethos-identity/users/roles",
    { ...creds, method: "POST", body: JSON.stringify({ email, roles }) },
  );

export const setUserState = (email: string, disabled: boolean) =>
  mcFetch<{ ok: boolean; error?: string; email?: string; disabled?: boolean }>(
    "/api/v1/aethos-identity/users/state",
    { ...creds, method: "POST", body: JSON.stringify({ email, disabled }) },
  );
