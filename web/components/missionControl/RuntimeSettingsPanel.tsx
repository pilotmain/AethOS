"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchRuntimeConfig,
  revertRuntimeConfig,
  setRuntimeConfig,
  type RuntimeSetting,
  type RuntimeSettingsGroup,
} from "@/lib/missionControl/runtimeConfigApi";
import {
  mcButtonSecondaryStyle,
  mcColors,
  mcInputStyle,
  mcPanelSectionStyle,
} from "@/lib/missionControl/layout";

function asBool(value: unknown): boolean {
  return value === true || value === "true" || value === 1 || value === "1";
}

export function RuntimeSettingsPanel() {
  const [groups, setGroups] = useState<RuntimeSettingsGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const res = await fetchRuntimeConfig();
      setGroups(res.groups ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load settings");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const write = useCallback(
    async (setting: RuntimeSetting, value: unknown) => {
      setBusy(setting.key);
      setNotice(null);
      setError(null);
      try {
        const res = await setRuntimeConfig(setting.key, value);
        if (res.restart_required) {
          setNotice(`${setting.label} saved — restart required to take effect.`);
        } else {
          setNotice(`${setting.label} saved.`);
        }
        await load();
      } catch (e) {
        setError(parseConfigError(e, setting.label));
      } finally {
        setBusy(null);
      }
    },
    [load],
  );

  const revert = useCallback(
    async (setting: RuntimeSetting) => {
      setBusy(setting.key);
      setNotice(null);
      setError(null);
      try {
        await revertRuntimeConfig(setting.key);
        setNotice(`${setting.label} reverted to default.`);
        await load();
      } catch (e) {
        setError(parseConfigError(e, setting.label));
      } finally {
        setBusy(null);
      }
    },
    [load],
  );

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Settings</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Configure AethOS capabilities here — no `.env` access needed. Changes persist and take
            effect immediately. Secrets (API keys, tokens) go to Connections; governance flags stay
            operator-only.
          </p>
        </div>
        <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, marginTop: 12, fontSize: 13 }}>{error}</p> : null}
      {notice ? <p style={{ color: mcColors.green, marginTop: 12, fontSize: 13 }}>{notice}</p> : null}

      {groups.map((group) => (
        <div key={group.group} style={{ marginTop: 20 }}>
          <h3
            style={{
              margin: "0 0 8px",
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              color: mcColors.textMuted,
            }}
          >
            {group.group}
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {group.settings.map((setting) => (
              <SettingRow
                key={setting.key}
                setting={setting}
                busy={busy === setting.key}
                onWrite={write}
                onRevert={revert}
              />
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

function SettingRow({
  setting,
  busy,
  onWrite,
  onRevert,
}: {
  setting: RuntimeSetting;
  busy: boolean;
  onWrite: (s: RuntimeSetting, value: unknown) => void;
  onRevert: (s: RuntimeSetting) => void;
}) {
  const [draft, setDraft] = useState<string>(setting.value == null ? "" : String(setting.value));

  useEffect(() => {
    setDraft(setting.value == null ? "" : String(setting.value));
  }, [setting.value]);

  const overridden = setting.source === "runtime_store";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 12,
        padding: "10px 14px",
        borderRadius: 10,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.18)",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600 }}>
          {setting.label}
          {overridden ? (
            <span style={{ marginLeft: 8, fontSize: 10, color: mcColors.cyan }}>· custom</span>
          ) : (
            <span style={{ marginLeft: 8, fontSize: 10, color: mcColors.textDim }}>· default</span>
          )}
        </div>
        <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 2 }}>{setting.description}</div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
        {setting.kind === "bool" ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => onWrite(setting, !asBool(setting.value))}
            style={{
              ...mcButtonSecondaryStyle,
              minWidth: 64,
              color: asBool(setting.value) ? mcColors.green : mcColors.textMuted,
              borderColor: asBool(setting.value) ? mcColors.green : mcColors.borderSubtle,
            }}
          >
            {asBool(setting.value) ? "On" : "Off"}
          </button>
        ) : setting.kind === "enum" ? (
          <select
            value={String(setting.value ?? "")}
            disabled={busy}
            onChange={(e) => onWrite(setting, e.target.value)}
            style={{ ...mcInputStyle, minWidth: 140 }}
          >
            {setting.options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        ) : (
          <>
            <input
              value={draft}
              disabled={busy}
              onChange={(e) => setDraft(e.target.value)}
              style={{ ...mcInputStyle, minWidth: 200 }}
            />
            <button type="button" disabled={busy} onClick={() => onWrite(setting, draft)} style={mcButtonSecondaryStyle}>
              Save
            </button>
          </>
        )}
        {overridden ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => onRevert(setting)}
            style={{ ...mcButtonSecondaryStyle, color: mcColors.textMuted }}
            title="Revert to .env / default"
          >
            Reset
          </button>
        ) : null}
      </div>
    </div>
  );
}

function parseConfigError(e: unknown, label: string): string {
  const raw = e instanceof Error ? e.message : String(e);
  try {
    const parsed = JSON.parse(raw);
    const detail = parsed?.detail;
    if (detail?.message) return `${label}: ${detail.message}`;
  } catch {
    /* not JSON */
  }
  return `${label}: ${raw}`;
}
