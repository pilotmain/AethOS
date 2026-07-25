"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  disableDemoMode,
  enableDemoMode,
  fetchDemoStatus,
  fetchEnterpriseConfig,
  fetchEnterpriseDoctor,
  fetchEnterpriseHealth,
  fetchSafeDefaults,
  fetchSetupWizard,
  type DoctorCheck,
  type HealthDashboard,
  type SetupStep,
} from "@/lib/missionControl/enterpriseApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const statusColor = (s?: string) => {
  if (s === "PASS" || s === "healthy" || s === "done") return mcColors.cyan;
  if (s === "WARNING" || s === "degraded") return mcColors.amber;
  if (s === "FAIL" || s === "unhealthy") return mcColors.red;
  return mcColors.textMuted;
};

const titles: Record<string, string> = {
  "enterprise-doctor": "Environment Doctor",
  "enterprise-setup-wizard": "First-Run Setup",
  "enterprise-config": "Configuration Center",
  "enterprise-health": "Operational Health",
  "enterprise-demo": "Demo Mode",
};

function CheckCard({ check }: { check: DoctorCheck }) {
  return (
    <div style={cardStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <span style={{ fontWeight: 600 }}>{check.name}</span>
        <span style={{ color: statusColor(check.status), fontSize: 11 }}>{check.status}</span>
      </div>
      <div style={{ color: mcColors.textDim, marginTop: 4, fontSize: 12 }}>{check.detail}</div>
      {check.fix_hint ? <div style={{ color: mcColors.textMuted, marginTop: 4, fontSize: 11 }}>Fix: {check.fix_hint}</div> : null}
      {check.actionable?.next_command ? (
        <div style={{ color: mcColors.amber, marginTop: 4, fontSize: 11 }}>Next: {check.actionable.next_command}</div>
      ) : null}
    </div>
  );
}

export function EnterpriseOperationsPanel({ view }: Props) {
  const [doctor, setDoctor] = useState<{ checks?: DoctorCheck[]; overall?: string; summary?: string } | null>(null);
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [health, setHealth] = useState<HealthDashboard | null>(null);
  const [wizard, setWizard] = useState<{ steps?: SetupStep[]; progress?: number; next_step?: SetupStep } | null>(null);
  const [demo, setDemo] = useState<{ enabled?: boolean; label?: string; overlay?: Record<string, unknown> } | null>(null);
  const [safeDefaults, setSafeDefaults] = useState<{ violations?: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "enterprise-doctor") setDoctor(await fetchEnterpriseDoctor());
      else if (view === "enterprise-config") setConfig(await fetchEnterpriseConfig());
      else if (view === "enterprise-health") setHealth(await fetchEnterpriseHealth());
      else if (view === "enterprise-setup-wizard") setWizard(await fetchSetupWizard());
      else if (view === "enterprise-demo") setDemo(await fetchDemoStatus());
      if (view === "enterprise-config") setSafeDefaults(await fetchSafeDefaults());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load enterprise state");
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  const onDemoToggle = async (enable: boolean) => {
    setBusy(true);
    try {
      if (enable) await enableDemoMode();
      else await disableDemoMode();
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{titles[view] ?? "Enterprise Readiness"}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Clarity, safe defaults, and operational confidence for onboarding.
          </p>
        </div>
        <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {view === "enterprise-doctor" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600, color: statusColor(doctor?.overall) }}>Overall: {doctor?.overall ?? "—"}</div>
            <div style={{ color: mcColors.textDim, marginTop: 4 }}>{doctor?.summary}</div>
            <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 6 }}>CLI: aethos doctor</div>
          </div>
          {(doctor?.checks ?? []).map((c, i) => (
            <CheckCard key={c.name || i} check={c} />
          ))}
        </div>
      )}

      {view === "enterprise-setup-wizard" && wizard && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            Progress: {Math.round((wizard.progress ?? 0) * 100)}% · Next: {wizard.next_step?.title ?? "Complete"}
          </div>
          {(wizard.steps ?? []).map((step) => (
            <div key={step.id} style={{ ...cardStyle, borderLeft: `3px solid ${statusColor(step.completed ? "done" : "WARNING")}` }}>
              <div style={{ fontWeight: 600 }}>{step.title}</div>
              <div style={{ fontSize: 11, color: mcColors.textDim }}>{step.status?.toUpperCase()} · {step.doc}</div>
            </div>
          ))}
        </div>
      )}

      {view === "enterprise-config" && config && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>.env: {(config.env as { env_present?: boolean })?.env_present ? "present" : "missing"}</div>
            <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>
              Enabled: {((config.enabled_features as string[]) ?? []).join(", ") || "none"}
            </div>
            <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>
              Disabled (safe): {((config.disabled_features as string[]) ?? []).slice(0, 6).join(", ")}
            </div>
            <div style={{ fontSize: 11, color: mcColors.amber, marginTop: 6 }}>
              {(config.env as { restart_required_hint?: string })?.restart_required_hint}
            </div>
          </div>
          {safeDefaults?.violations?.length ? (
            <div style={{ ...cardStyle, borderColor: mcColors.amber }}>
              Safe default violations: {safeDefaults.violations.join("; ")}
            </div>
          ) : (
            <div style={cardStyle}>Safe defaults verified</div>
          )}
          <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 11, color: mcColors.textMuted }}>
            {JSON.stringify(config.settings_preview, null, 2)}
          </pre>
        </div>
      )}

      {view === "enterprise-health" && health && (
        <div style={{ marginTop: 16 }}>
          <div style={{ ...cardStyle, borderLeft: `3px solid ${statusColor(health.overall)}` }}>
            <div style={{ fontWeight: 600 }}>System: {health.overall}</div>
            <div style={{ color: mcColors.textDim, marginTop: 4 }}>Doctor: {health.doctor_overall}</div>
          </div>
          {Object.entries(health.components ?? {}).map(([key, comp]) => (
            <div key={key} style={cardStyle}>
              <span style={{ fontWeight: 600 }}>{key.replace(/_/g, " ")}</span>
              <span style={{ float: "right", color: statusColor(comp.status), fontSize: 11 }}>{comp.status}</span>
              {comp.global_score != null ? (
                <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>Score: {comp.global_score}</div>
              ) : null}
              {comp.detail ? <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>{comp.detail}</div> : null}
            </div>
          ))}
        </div>
      )}

      {view === "enterprise-demo" && (
        <div style={{ marginTop: 16 }}>
          <div style={{ ...cardStyle, borderColor: demo?.enabled ? mcColors.cyan : mcColors.borderSubtle }}>
            <div style={{ fontWeight: 600, color: mcColors.cyan }}>{demo?.label ?? "DEMO DATA"}</div>
            <div style={{ marginTop: 4 }}>Status: {demo?.enabled ? "enabled" : "disabled"}</div>
            <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 6 }}>
              Synthetic provider events, recommendations, research, preflights, and replay — no real credentials required.
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button type="button" disabled={busy || demo?.enabled} onClick={() => onDemoToggle(true)} style={mcButtonSecondaryStyle}>
                Enable demo
              </button>
              <button type="button" disabled={busy || !demo?.enabled} onClick={() => onDemoToggle(false)} style={mcButtonSecondaryStyle}>
                Disable demo
              </button>
            </div>
          </div>
          {demo?.enabled && demo.overlay ? (
            <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 11, color: mcColors.textMuted }}>
              {JSON.stringify(demo.overlay, null, 2)}
            </pre>
          ) : null}
        </div>
      )}
    </section>
  );
}
