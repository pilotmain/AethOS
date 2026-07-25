"use client";

import { useCallback, useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type GovernanceDiagnostics = {
  mutation_execution_enabled?: boolean;
  railway_greenfield_mutation_kill_switch?: boolean;
};

export function GovernanceKillSwitchPanel() {
  const [diag, setDiag] = useState<GovernanceDiagnostics | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const res = await fetch(`${apiBase()}/api/v1/governance/diagnostics`);
    if (!res.ok) return;
    const payload = await res.json();
    setDiag(payload?.diagnostics ?? null);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function setOverride(key: string, value: boolean) {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/governance/overrides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(String(err.detail ?? res.statusText));
      }
      setMessage(`${key} → ${value ? "ON" : "OFF"} (runtime override saved)`);
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Failed to save override");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={{ ...mcPanelSectionStyle, marginTop: 16 }}>
      <h3 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 600 }}>Governance kill switches</h3>
      <p style={{ margin: "0 0 12px", fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
        Emergency stops write to <code>data/governance_runtime_overrides.json</code> — not chat and not .env.
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        <KillToggle
          label="All mutations"
          active={Boolean(diag?.mutation_execution_enabled)}
          onEnable={() => void setOverride("mutation_execution_enabled", true)}
          onDisable={() => void setOverride("mutation_execution_enabled", false)}
          busy={busy}
        />
        <KillToggle
          label="Railway greenfield kill switch"
          active={Boolean(diag?.railway_greenfield_mutation_kill_switch)}
          onEnable={() => void setOverride("railway_greenfield_mutation_kill_switch", true)}
          onDisable={() => void setOverride("railway_greenfield_mutation_kill_switch", false)}
          busy={busy}
        />
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()} disabled={busy}>
          Refresh
        </button>
      </div>
      {message ? (
        <p style={{ margin: "10px 0 0", fontSize: 12, color: mcColors.amber }} role="status">
          {message}
        </p>
      ) : null}
    </section>
  );
}

function KillToggle({
  label,
  active,
  onEnable,
  onDisable,
  busy,
}: {
  label: string;
  active: boolean;
  onEnable: () => void;
  onDisable: () => void;
  busy: boolean;
}) {
  return (
    <div
      style={{
        padding: "10px 12px",
        borderRadius: 8,
        border: `1px solid ${active ? mcColors.amber : mcColors.border}`,
        minWidth: 220,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 12, color: mcColors.textMuted, marginBottom: 8 }}>Effective: {active ? "ON" : "OFF"}</div>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="button" style={mcButtonSecondaryStyle} disabled={busy} onClick={onDisable}>
          Stop
        </button>
        <button type="button" style={mcButtonSecondaryStyle} disabled={busy} onClick={onEnable}>
          Allow
        </button>
      </div>
    </div>
  );
}
