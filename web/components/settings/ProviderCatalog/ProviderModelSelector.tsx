"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchProviderModelSelection,
  saveProviderModelSelection,
  type ProviderModel,
} from "@/lib/missionControl/modelSelectionApi";
import { mcButtonSecondaryStyle, mcColors, mcInputStyle } from "@/lib/missionControl/layout";

/** Checklist of a connected model provider's models + a custom-model-id field.
 * Persists the enabled set + custom ids in the runtime config store (§1). */
export function ProviderModelSelector({
  provider,
  previewOnly = false,
}: {
  provider: string;
  previewOnly?: boolean;
}) {
  const [models, setModels] = useState<ProviderModel[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [customId, setCustomId] = useState("");

  const load = useCallback(async () => {
    try {
      setError(null);
      const res = await fetchProviderModelSelection(provider);
      setModels(res.models ?? []);
      setLoaded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load models");
    }
  }, [provider]);

  useEffect(() => {
    void load();
  }, [load]);

  const persist = useCallback(
    async (next: ProviderModel[]) => {
      if (previewOnly) return;
      setSaving(true);
      setNotice(null);
      setError(null);
      try {
        const enabled = next.filter((m) => m.enabled).map((m) => m.model_id);
        const custom = next.filter((m) => m.custom).map((m) => m.model_id);
        const res = await saveProviderModelSelection(provider, enabled, custom);
        setModels(res.models ?? next);
        setNotice("Models saved.");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to save models");
      } finally {
        setSaving(false);
      }
    },
    [provider, previewOnly],
  );

  const toggle = useCallback(
    (modelId: string) => {
      if (previewOnly) return;
      const next = models.map((m) => (m.model_id === modelId ? { ...m, enabled: !m.enabled } : m));
      setModels(next);
      void persist(next);
    },
    [models, persist, previewOnly],
  );

  const addCustom = useCallback(() => {
    if (previewOnly) return;
    const id = customId.trim();
    if (!id) return;
    if (models.some((m) => m.model_id === id)) {
      setCustomId("");
      return;
    }
    const next = [...models, { model_id: id, label: id, enabled: true, custom: true }];
    setCustomId("");
    setModels(next);
    void persist(next);
  }, [customId, models, persist, previewOnly]);

  if (!loaded && !error) {
    return <p style={{ fontSize: 12, color: mcColors.textMuted }}>Loading models…</p>;
  }

  const enabledCount = models.filter((m) => m.enabled).length;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 8,
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color: mcColors.text }}>
          {previewOnly ? "Models preview" : `Models (${enabledCount} enabled)`}
        </span>
        {saving ? <span style={{ fontSize: 11, color: mcColors.textMuted }}>Saving…</span> : null}
      </div>
      <p style={{ margin: "0 0 10px", fontSize: 11, color: mcColors.textMuted }}>
        {previewOnly
          ? "These models unlock when you add a key. All are enabled by default."
          : "Tick the models to expose in the picker and arbiter. Add a custom model id (e.g. "}
        {!previewOnly ? (
          <>
            <code>o3</code>, <code>deepseek-reasoner</code>) for newer models.
          </>
        ) : null}
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {models.map((m) => (
          <label
            key={m.model_id}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 10px",
              borderRadius: 6,
              fontSize: 11,
              cursor: "pointer",
              background: m.enabled ? "rgba(8,145,178,0.18)" : "rgba(0,0,0,0.25)",
              border: `1px solid ${m.enabled ? mcColors.cyan : mcColors.borderSubtle}`,
              color: m.enabled ? mcColors.text : mcColors.textMuted,
            }}
          >
            <input
              type="checkbox"
              checked={m.enabled}
              disabled={previewOnly}
              onChange={() => toggle(m.model_id)}
              style={{ accentColor: "var(--aethos-accent)" }}
            />
            {m.label}
            {m.custom ? (
              <span style={{ fontSize: 9, color: mcColors.textDim }}>custom</span>
            ) : null}
          </label>
        ))}
      </div>

      {!previewOnly ? (
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <input
            value={customId}
            placeholder="Add custom model id…"
            onChange={(e) => setCustomId(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addCustom();
              }
            }}
            style={{ ...mcInputStyle, flex: 1, minWidth: 0 }}
          />
          <button type="button" onClick={addCustom} disabled={saving} style={mcButtonSecondaryStyle}>
            Add
          </button>
        </div>
      ) : null}

      {notice ? (
        <p style={{ margin: "8px 0 0", fontSize: 11, color: mcColors.green }}>{notice}</p>
      ) : null}
      {error ? <p style={{ margin: "8px 0 0", fontSize: 11, color: mcColors.red }}>{error}</p> : null}
    </div>
  );
}
