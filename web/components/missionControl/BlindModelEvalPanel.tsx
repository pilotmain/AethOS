"use client";

import { useEffect, useState } from "react";

import { runBlindEval } from "@/lib/missionControl/phase4Api";
import { fetchModelCatalog, type ModelCatalogEntry } from "@/lib/chat/modelSelection";
import { mcButtonPrimaryStyle, mcColors, mcGradientTextStyle, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function BlindModelEvalPanel() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<Awaited<ReturnType<typeof runBlindEval>>>(null);
  const [busy, setBusy] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [models, setModels] = useState<ModelCatalogEntry[]>([]);
  const [modelA, setModelA] = useState("default");
  const [modelB, setModelB] = useState("default");

  useEffect(() => {
    void (async () => {
      try {
        const snapshot = await fetchModelCatalog("blind-eval");
        setModels(snapshot.models ?? []);
      } catch {
        setModels([]);
      }
    })();
  }, []);

  const run = async () => {
    const q = prompt.trim();
    if (q.length < 8) return;
    setBusy(true);
    setRevealed(false);
    try {
      setResult(await runBlindEval(q, modelA, modelB));
    } finally {
      setBusy(false);
    }
  };

  const slots = (result?.blind_slots as { slot_id?: string; text?: string }[]) ?? [];
  const revealMap = (result?.reveal_map as Record<string, string>) ?? {};
  const pickerStyle = {
    flex: 1,
    minWidth: 0,
    padding: "8px 10px",
    borderRadius: 8,
    border: `1px solid ${mcColors.borderSubtle}`,
    background: "rgba(0,0,0,0.35)",
    color: mcColors.text,
    fontSize: 12,
  } as const;

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 22, fontWeight: 750, letterSpacing: "-0.02em", width: "fit-content", ...mcGradientTextStyle }}>
        Blind model eval
      </h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 560 }}>
        Compare two models on their real providers without labels — reveal the true mapping after you pick a winner.
      </p>
      <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
        <label style={{ flex: 1, minWidth: 200, fontSize: 11, color: mcColors.textDim }}>
          Slot A model
          <select value={modelA} onChange={(e) => setModelA(e.target.value)} style={{ ...pickerStyle, marginTop: 4, width: "100%" }}>
            <option value="default">Default (.env)</option>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ flex: 1, minWidth: 200, fontSize: 11, color: mcColors.textDim }}>
          Slot B model
          <select value={modelB} onChange={(e) => setModelB(e.target.value)} style={{ ...pickerStyle, marginTop: 4, width: "100%" }}>
            <option value="default">Default (.env)</option>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={3}
        placeholder="Compare approaches for deploying AethOS on Railway vs Vercel…"
        style={{
          width: "100%",
          boxSizing: "border-box",
          padding: "12px 14px",
          borderRadius: 10,
          border: `1px solid ${mcColors.borderSubtle}`,
          background: "rgba(0,0,0,0.35)",
          color: mcColors.text,
          fontSize: 14,
        }}
      />
      <button type="button" style={{ ...mcButtonPrimaryStyle, marginTop: 10 }} disabled={busy} onClick={() => void run()}>
        {busy ? "Running…" : "Run blind eval"}
      </button>
      {slots.length > 0 ? (
        <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {slots.map((slot) => (
            <div
              key={slot.slot_id}
              style={{
                padding: 12,
                borderRadius: 12,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.22)",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 700, color: mcColors.cyan, marginBottom: 8 }}>
                {revealed ? `${slot.slot_id} → ${revealMap[slot.slot_id ?? ""] ?? "?"}` : slot.slot_id}
              </div>
              <pre style={{ margin: 0, fontSize: 11, whiteSpace: "pre-wrap", color: mcColors.textMuted }}>{slot.text}</pre>
            </div>
          ))}
        </div>
      ) : null}
      {slots.length > 0 && !revealed ? (
        <button type="button" style={{ marginTop: 12, fontSize: 12, color: mcColors.cyan, background: "none", border: "none", cursor: "pointer" }} onClick={() => setRevealed(true)}>
          Reveal model mapping →
        </button>
      ) : null}
    </section>
  );
}
