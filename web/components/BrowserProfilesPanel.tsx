"use client";

import { useCallback, useState } from "react";

import {
  forgetBrowserProfile,
  testBrowserProfile,
  type BrowserProfileRecord,
  type BrowserProfilesResponse,
} from "@/lib/missionControl/browserProfiles";
import { formatMcPanelError } from "@/lib/missionControl/panelError";

type Props = {
  data: BrowserProfilesResponse | null;
  onRefresh: () => void;
};

const btnBase = {
  marginTop: 8,
  borderRadius: 8,
  padding: "6px 12px",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};

function ProfileCard({
  profile,
  busyId,
  onForget,
  onTest,
}: {
  profile: BrowserProfileRecord;
  busyId: string | null;
  onForget: (id: string) => void;
  onTest: (id: string) => void;
}) {
  const lastUsed =
    profile.last_used_at != null
      ? new Date(profile.last_used_at * 1000).toLocaleString()
      : "never";
  return (
    <li
      style={{
        padding: 12,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
        fontSize: 13,
      }}
    >
      <div style={{ fontWeight: 600 }}>{profile.site}</div>
      <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
        Status: {profile.status} · Scope: {profile.scope} · Read-only:{" "}
        {profile.read_only_allowed ? "yes" : "no"}
      </div>
      {profile.status === "expired" && (
        <p style={{ margin: "8px 0 0", fontSize: 12, color: "var(--aethos-warn)", lineHeight: 1.5 }}>
          Session expired — open a supervised Vercel session, log in manually, then save again. Read-only
          inspection will not use this profile until it is active.
        </p>
      )}
      <div style={{ color: "var(--aethos-text-dim)", marginTop: 4, fontSize: 11 }}>
        <code>{profile.profile_id}</code> · last used {lastUsed}
      </div>
      <div style={{ color: "var(--aethos-text-dim)", marginTop: 6, fontSize: 11, lineHeight: 1.5 }}>
        Session: {profile.session_type ?? "persistent"} · Expires: {profile.expires_label ?? "until revoked"}
        <br />
        Read-only: {profile.read_only_allowed ? "yes" : "no"} · Write actions:{" "}
        {profile.write_actions_allowed ? "yes" : "no"}
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
        <button
          type="button"
          disabled={busyId === profile.profile_id}
          onClick={() => onTest(profile.profile_id)}
          style={{
            ...btnBase,
            marginTop: 0,
            border: "1px solid rgba(96,165,250,0.35)",
            background: "rgba(59,130,246,0.1)",
            color: "var(--aethos-accent)",
          }}
        >
          {busyId === profile.profile_id ? "Testing…" : "Test session"}
        </button>
        <button
          type="button"
          disabled={busyId === profile.profile_id}
          onClick={() => onForget(profile.profile_id)}
          style={{
            ...btnBase,
            marginTop: 0,
            border: "1px solid rgba(248,113,113,0.35)",
            background: "rgba(248,113,113,0.1)",
            color: "var(--aethos-danger)",
          }}
        >
          Forget session
        </button>
      </div>
    </li>
  );
}

export function BrowserProfilesPanel({ data, onRefresh }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [panelError, setPanelError] = useState("");
  const [testMsg, setTestMsg] = useState("");

  const run = useCallback(
    async (id: string, fn: (id: string) => Promise<unknown>) => {
      setBusyId(id);
      setPanelError("");
      setTestMsg("");
      try {
        const out = await fn(id);
        if (out && typeof out === "object" && "result" in out) {
          const r = (out as { result: { message?: string; ok?: boolean } }).result;
          setTestMsg(r.message ?? (r.ok ? "Session OK" : "Session check failed"));
        }
        onRefresh();
      } catch (e) {
        setPanelError(formatMcPanelError(e instanceof Error ? e.message : "Request failed"));
      } finally {
        setBusyId(null);
      }
    },
    [onRefresh],
  );

  const profiles = (data?.profiles ?? []).filter((p) => p.status !== "revoked");

  return (
    <section style={{ marginBottom: 20 }}>
      <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>Saved browser sessions</h2>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: "var(--aethos-text-muted)" }}>
        Opt-in only — no passwords or cookie values shown. Write actions (restart/redeploy) are not
        enabled.
      </p>
      {panelError && (
        <p style={{ color: "var(--aethos-warn)", fontSize: 12, marginBottom: 8 }} role="status">
          {panelError}
        </p>
      )}
      {testMsg && (
        <p style={{ color: "var(--aethos-ok)", fontSize: 12, marginBottom: 8 }} role="status">
          {testMsg}
        </p>
      )}
      {data?.profile_store_path && (
        <p style={{ color: "var(--aethos-text-dim)", fontSize: 11, marginBottom: 8 }}>
          Store: <code>{data.profile_store_path}</code>
          {typeof data.count === "number" ? ` · ${data.count} profile(s)` : null}
        </p>
      )}
      {profiles.length === 0 ? (
        <p style={{ color: "var(--aethos-text-dim)", fontSize: 13 }}>No saved sessions yet.</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
          {profiles.map((p) => (
            <ProfileCard
              key={p.profile_id}
              profile={p}
              busyId={busyId}
              onForget={(id) => void run(id, forgetBrowserProfile)}
              onTest={(id) => void run(id, testBrowserProfile)}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
