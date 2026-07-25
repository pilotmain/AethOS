"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  type AethosRole,
  type AethosUser,
  type SessionResponse,
  fetchSession,
  fetchUsers,
  setUserRoles,
  setUserState,
} from "@/lib/missionControl/usersApi";

const ROLE_HELP: Record<AethosRole, string> = {
  admin: "Full control incl. user/role management",
  approver: "Grant/deny approvals (separation of duties)",
  operator: "Run actions, mutations, spawn agents — and add connections & approve within their own account",
  read_only: "Read everything, mutate nothing",
};

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: mcColors.bgCard,
  fontSize: 13,
} as const;

const chip = (active: boolean) => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "3px 9px",
  marginRight: 6,
  marginBottom: 6,
  borderRadius: 999,
  border: `1px solid ${active ? mcColors.cyan : mcColors.borderSubtle}`,
  background: active ? "rgba(34,211,238,0.12)" : "transparent",
  color: active ? mcColors.text : mcColors.textMuted,
  cursor: "pointer",
  fontSize: 12,
  userSelect: "none" as const,
});

export function UsersRolesPanel() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [users, setUsers] = useState<AethosUser[]>([]);
  const [validRoles, setValidRoles] = useState<AethosRole[]>([
    "admin",
    "approver",
    "operator",
    "read_only",
  ]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const canManage = useMemo(
    () => (session?.user?.permissions ?? []).includes("manage_users"),
    [session],
  );

  const load = useCallback(async () => {
    setError(null);
    try {
      const s = await fetchSession();
      setSession(s);
      if (!s.auth_enabled) return;
      const list = await fetchUsers();
      if (list.ok) {
        setUsers(list.users);
        if (list.valid_roles?.length) setValidRoles(list.valid_roles);
      } else {
        setError(list.error === "forbidden" ? "You need admin (manage_users) to view users." : list.error ?? "Failed to load users.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load users & roles.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleRole = useCallback(
    async (user: AethosUser, role: AethosRole) => {
      if (!canManage || busy) return;
      const has = user.roles.includes(role);
      const next = has ? user.roles.filter((r) => r !== role) : [...user.roles, role];
      if (next.length === 0) {
        setError("A user must have at least one role.");
        return;
      }
      setBusy(true);
      setError(null);
      setNotice(null);
      try {
        const res = await setUserRoles(user.email, next);
        if (res.ok) {
          setNotice(`Updated roles for ${user.email}.`);
          await load();
        } else {
          setError(res.error ?? "Role update failed.");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Role update failed.");
      } finally {
        setBusy(false);
      }
    },
    [canManage, busy, load],
  );

  const toggleDisabled = useCallback(
    async (user: AethosUser) => {
      if (!canManage || busy) return;
      setBusy(true);
      setError(null);
      setNotice(null);
      try {
        const res = await setUserState(user.email, !user.disabled);
        if (res.ok) {
          setNotice(`${user.email} ${res.disabled ? "disabled" : "enabled"}.`);
          await load();
        } else {
          setError(res.error ?? "State change failed.");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "State change failed.");
      } finally {
        setBusy(false);
      }
    },
    [canManage, busy, load],
  );

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Users &amp; Roles</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Least-privilege RBAC for human users. The API is authoritative — read-only users cannot
        approve or mutate even if a control is shown. Role changes take effect immediately.
      </p>

      {session && !session.auth_enabled ? (
        <div style={cardStyle}>
          Authentication is disabled (<code>AUTH_ENABLED=false</code>), so AethOS runs as a single
          trusted local operator. Enable auth to manage multiple users and roles.
        </div>
      ) : null}

      {error ? <div style={{ color: mcColors.red, marginBottom: 8 }}>{error}</div> : null}
      {notice ? <div style={{ color: mcColors.green, marginBottom: 8 }}>{notice}</div> : null}

      {session?.auth_enabled && !canManage ? (
        <div style={cardStyle}>
          You are signed in as <strong>{session.user?.email}</strong> with roles{" "}
          {(session.user?.roles ?? []).join(", ") || "—"}. Admin (manage_users) is required to edit
          users.
        </div>
      ) : null}

      {session?.auth_enabled && canManage
        ? users.map((user) => (
            <div key={user.email} style={cardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>{user.email}</strong>
                  {user.disabled ? (
                    <span style={{ color: mcColors.red, marginLeft: 8, fontSize: 12 }}>disabled</span>
                  ) : null}
                  <div style={{ color: mcColors.textMuted, fontSize: 12 }}>
                    {user.auth ?? "local"} · MFA {user.mfa_enrolled ? "on" : "off"}
                  </div>
                </div>
                <button
                  onClick={() => void toggleDisabled(user)}
                  disabled={busy}
                  style={{
                    padding: "5px 10px",
                    borderRadius: 8,
                    border: `1px solid ${mcColors.borderSubtle}`,
                    background: "transparent",
                    color: user.disabled ? mcColors.green : mcColors.red,
                    cursor: busy ? "not-allowed" : "pointer",
                    fontSize: 12,
                  }}
                >
                  {user.disabled ? "Enable" : "Disable"}
                </button>
              </div>
              <div style={{ marginTop: 10 }}>
                {validRoles.map((role) => (
                  <span
                    key={role}
                    role="button"
                    tabIndex={0}
                    aria-pressed={user.roles.includes(role)}
                    title={ROLE_HELP[role]}
                    onClick={() => void toggleRole(user, role)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        void toggleRole(user, role);
                      }
                    }}
                    style={chip(user.roles.includes(role))}
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          ))
        : null}
    </div>
  );
}
