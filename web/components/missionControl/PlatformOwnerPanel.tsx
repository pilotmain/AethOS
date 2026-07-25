"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  type OwnerUserRow,
  extendOwnerUser,
  fetchOwnerUsers,
  grantOwnerUser,
  reinstateOwnerUser,
  revokeOwnerUser,
} from "@/lib/missionControl/platformOwnerApi";

const rowStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: mcColors.bgCard,
  fontSize: 13,
} as const;

function formatTs(ts: number | null | undefined): string {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

export function PlatformOwnerPanel() {
  const [users, setUsers] = useState<OwnerUserRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await fetchOwnerUsers();
      if (res.ok) {
        setUsers(res.users);
      } else {
        setError(res.error ?? "Failed to load users.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load users.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const run = async (fn: () => Promise<{ ok: boolean; error?: string }>) => {
    setBusy(true);
    setNotice(null);
    setError(null);
    try {
      const res = await fn();
      if (!res.ok) {
        setError(res.error ?? "Request failed.");
      } else {
        setNotice("Updated.");
        await load();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  };

  const activeStatuses = new Set(["active", "trial"]);
  const total = users.length;
  const active = users.filter((u) => activeStatuses.has(String(u.status)) && !u.disabled).length;
  const onlineNow = users.filter((u) => (u.session_count ?? 0) > 0).length;

  const stats: { label: string; value: number }[] = [
    { label: "Total users", value: total },
    { label: "Active beta", value: active },
    { label: "Online now", value: onlineNow },
  ];

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>Owner console</h2>
      <p style={{ margin: "0 0 16px", fontSize: 13, color: mcColors.textMuted }}>
        Grant time-boxed beta access, extend trials, and revoke instantly. Only visible to the platform
        owner (Railway env). To restrict what a user can <em>do</em> (read-only, operator, approver), use{" "}
        <strong>Users &amp; roles</strong> in the sidebar.
      </p>
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        {stats.map((s) => (
          <div
            key={s.label}
            style={{
              flex: "1 1 120px",
              padding: "12px 14px",
              borderRadius: 10,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: mcColors.bgCard,
            }}
          >
            <div style={{ fontSize: 24, fontWeight: 700 }}>{s.value}</div>
            <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>
      {error ? <p style={{ color: "#f87171", fontSize: 13 }}>{error}</p> : null}
      {notice ? <p style={{ color: mcColors.cyan, fontSize: 13 }}>{notice}</p> : null}
      {users.length === 0 ? (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No users yet.</p>
      ) : (
        users.map((u) => (
          <div key={u.user_id} style={rowStyle}>
            <div style={{ fontWeight: 600 }}>{u.email}</div>
            <div style={{ color: mcColors.textMuted, fontSize: 12, marginTop: 4 }}>
              {u.status} · plan {u.plan ?? "—"} · expires {formatTs(u.access_expires_at)} · sessions{" "}
              {u.session_count ?? 0}
            </div>
            <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 8 }}>
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  run(() =>
                    grantOwnerUser(u.user_id, { status: "trial", plan: "beta", trial_days: 30 }),
                  )
                }
              >
                Grant 30-day trial
              </button>
              <button type="button" disabled={busy} onClick={() => run(() => extendOwnerUser(u.user_id, 30))}>
                Extend 30 days
              </button>
              <button type="button" disabled={busy} onClick={() => run(() => reinstateOwnerUser(u.user_id))}>
                Reinstate
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => run(() => revokeOwnerUser(u.user_id))}
                style={{ color: "#f87171" }}
              >
                Revoke
              </button>
            </div>
          </div>
        ))
      )}
    </section>
  );
}
