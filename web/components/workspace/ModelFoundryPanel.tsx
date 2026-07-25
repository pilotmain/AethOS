"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  dismissServeRequest,
  recommendModels,
  serveModelPreflight,
  serveStatus,
  stopServe,
  type Hardware,
  type ModelFit,
  type ServeRequest,
} from "@/lib/workspace/foundryApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";
import { WorkspaceNav } from "@/components/workspace/WorkspaceNav";

const VERDICT_COLOR: Record<string, string> = {
  great: "var(--aethos-ok)",
  ok: "var(--aethos-accent)",
  tight: "var(--aethos-warn)",
  no: "var(--aethos-danger)",
};

const SERVE_STATUS_META: Record<string, { label: string; color: string }> = {
  pending_approval: { label: "Pending approval", color: "var(--aethos-warn)" },
  preflight: { label: "Pending approval", color: "var(--aethos-warn)" },
  starting: { label: "Starting runtime…", color: "var(--aethos-accent)" },
  downloading: { label: "Downloading", color: "var(--aethos-accent)" },
  served: { label: "Served (local)", color: "var(--aethos-ok)" },
  stopped: { label: "Stopped", color: "var(--aethos-text-dim)" },
};

export function ModelFoundryPanel() {
  const [hardware, setHardware] = useState<Hardware | null>(null);
  const [models, setModels] = useState<ModelFit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [served, setServed] = useState<string | null>(null);
  const [serveRequests, setServeRequests] = useState<ServeRequest[]>([]);
  const [autostart, setAutostart] = useState(false);
  const [autodownload, setAutodownload] = useState(false);

  const refreshServeStatus = useCallback(async () => {
    const res = await serveStatus();
    if (res.ok) {
      setServeRequests(res.serve_requests.filter((r) => r.status !== "stopped"));
      setAutostart(Boolean(res.autostart_enabled));
      setAutodownload(Boolean(res.autodownload_enabled));
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    const res = await recommendModels();
    if (!res.ok) setError(res.error || "load_failed");
    else {
      setError(null);
      setHardware(res.hardware ?? null);
      setModels(res.models);
    }
    setLoading(false);
    await refreshServeStatus();
  }, [refreshServeStatus]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Live-poll while a serve request is starting a runtime or downloading weights.
  const hasInProgress = serveRequests.some((r) => r.status === "starting" || r.status === "downloading");
  useEffect(() => {
    if (!hasInProgress) return;
    const timer = setInterval(() => {
      void refreshServeStatus();
    }, 2500);
    return () => clearInterval(timer);
  }, [hasInProgress, refreshServeStatus]);

  const requestServe = useCallback(
    async (modelId: string) => {
      const res = await serveModelPreflight(modelId);
      setServed(
        res.ok
          ? `Serve request recorded for ${modelId} — pending approval in Mission Control → Approvals. Approve it there to add it to the chat model picker.`
          : `Failed: ${res.error}`,
      );
      await refreshServeStatus();
    },
    [refreshServeStatus],
  );

  const requestStop = useCallback(
    async (req: ServeRequest) => {
      const res = await stopServe(req.id);
      setServed(
        res.ok
          ? `Governed stop recorded for ${req.label || req.model_id}. Stop the local runtime process to free the port.`
          : `Failed to stop: ${res.error}`,
      );
      await refreshServeStatus();
    },
    [refreshServeStatus],
  );

  const requestDismiss = useCallback(
    async (req: ServeRequest) => {
      const res = await dismissServeRequest(req.id);
      if (!res.ok) setServed(`Failed to dismiss: ${res.error}`);
      await refreshServeStatus();
    },
    [refreshServeStatus],
  );

  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS · WORKSPACE</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>Model Foundry</h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
              Scans your hardware and ranks open models by how well they fit your GPU/memory.
              Serving runs <strong>locally on this machine</strong> and{" "}
              <strong>requires your approval</strong> — a serve request is queued for approval and
              never auto-starts or downloads anything.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <Link href="/" style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              ← Chat
            </Link>
            <Link href={missionControlHref("home")} style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              Mission Control
            </Link>
          </div>
        </div>

        <WorkspaceNav active="foundry" />

        {error ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12, borderColor: "color-mix(in srgb, var(--aethos-danger) 45%, transparent)" }}>
            <p style={{ margin: 0, fontSize: 13, color: "var(--aethos-danger)" }}>
              {error === "model_foundry_disabled"
                ? "Model Foundry is turned off for this deployment. Ask AethOS in chat how to enable it."
                : `Error: ${error}`}
            </p>
          </section>
        ) : null}

        <section style={{ ...mcPanelSectionStyle, marginBottom: 12 }}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            On approval, this instance will{" "}
            <strong style={{ color: autostart ? mcColors.cyan : mcColors.textDim }}>
              {autostart ? "auto-start a local runtime" : "require a running runtime"}
            </strong>{" "}
            and{" "}
            <strong style={{ color: autodownload ? mcColors.cyan : mcColors.textDim }}>
              {autodownload ? "auto-download missing weights" : "require weights already pulled"}
            </strong>
            . {autostart || autodownload ? "Approval is the consent gate." : "Enable the MODEL_FOUNDRY_AUTOSTART/AUTODOWNLOAD flags to let approval do this."}
          </p>
        </section>

        {hardware?.ok && hardware.detection_unavailable ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 16, borderColor: "color-mix(in srgb, var(--aethos-warn) 45%, transparent)" }}>
            <h2 style={{ margin: "0 0 6px", fontSize: 14 }}>Hardware detection unavailable</h2>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
              Could not read total memory on this host ({hardware.system} · {hardware.arch}
              {hardware.cpu_count ? ` · ${hardware.cpu_count} CPUs` : ""}). Model fit is hidden
              rather than showing a misleading 0&nbsp;GB. Reinstall dependencies
              (<code style={{ fontSize: 12 }}>psutil</code>) and refresh.
            </p>
          </section>
        ) : hardware?.ok ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 16 }}>
            <h2 style={{ margin: "0 0 8px", fontSize: 14 }}>Detected hardware</h2>
            <div style={{ display: "flex", gap: 18, flexWrap: "wrap", fontSize: 13, color: mcColors.textMuted }}>
              <span>{hardware.system} · {hardware.arch}</span>
              <span>{hardware.cpu_count} CPUs</span>
              <span>{hardware.total_ram_gb} GB RAM</span>
              <span>{hardware.unified_memory ? "unified memory" : "discrete"}</span>
              <span style={{ color: mcColors.cyan }}>~{hardware.usable_vram_gb} GB usable VRAM</span>
            </div>
          </section>
        ) : null}

        {served ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.cyan }}>{served}</p>
          </section>
        ) : null}

        {serveRequests.length ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 16 }}>
            <h2 style={{ margin: "0 0 8px", fontSize: 14 }}>Serve requests</h2>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
              {serveRequests.map((req) => {
                const meta = SERVE_STATUS_META[req.status || ""] || { label: req.status || "—", color: mcColors.textMuted };
                const isServed = req.status === "served";
                return (
                  <li
                    key={req.id}
                    style={{
                      padding: "10px 12px",
                      borderRadius: 8,
                      border: `1px solid ${mcColors.border}`,
                      background: "rgba(0,0,0,0.2)",
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{req.label || req.model_id}</div>
                      <div style={{ fontSize: 11, color: mcColors.textDim }}>
                        {req.bind || "127.0.0.1"}:{req.port || 11434}
                        {isServed && req.endpoint ? ` · ${req.endpoint}` : ""}
                      </div>
                      {req.status === "downloading" ? (
                        <div style={{ marginTop: 6, maxWidth: 320 }}>
                          <div style={{ height: 6, borderRadius: 4, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
                            <div
                              style={{
                                height: "100%",
                                width: `${Math.max(2, Math.min(100, req.progress ?? 0))}%`,
                                background: mcColors.cyan,
                                transition: "width 0.4s ease",
                              }}
                            />
                          </div>
                        </div>
                      ) : null}
                      {req.status === "pending_approval" && req.error ? (
                        <div style={{ fontSize: 11, color: "var(--aethos-danger)", marginTop: 4 }}>Last attempt: {req.error}</div>
                      ) : null}
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: meta.color }}>
                      {meta.label}
                      {req.status === "downloading" ? ` ${req.progress ?? 0}%` : ""}
                    </span>
                    {isServed ? (
                      <button
                        type="button"
                        onClick={() => void requestStop(req)}
                        style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}
                        title="Record a governed stop and remove from the chat picker"
                      >
                        Stop serving
                      </button>
                    ) : (
                      <>
                        <Link
                          href={missionControlHref("approvals")}
                          style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}
                          title="Approve this serve request in Mission Control"
                        >
                          Review in Approvals
                        </Link>
                        {req.status === "pending_approval" || req.status === "preflight" ? (
                          <button
                            type="button"
                            onClick={() => void requestDismiss(req)}
                            style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}
                            title="Dismiss this pending serve request"
                          >
                            Dismiss
                          </button>
                        ) : null}
                      </>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>
        ) : null}

        <section style={mcPanelSectionStyle}>
          <h2 style={{ margin: "0 0 10px", fontSize: 14 }}>Model fit</h2>
          {loading ? <p style={{ fontSize: 12, color: mcColors.textMuted }}>Scanning…</p> : null}
          {!loading && hardware?.detection_unavailable ? (
            <p style={{ fontSize: 12, color: mcColors.textMuted }}>
              Hardware detection unavailable — model fit is hidden until memory can be read.
            </p>
          ) : null}
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
            {models.map((m) => (
              <li
                key={m.id}
                style={{
                  padding: "10px 12px",
                  borderRadius: 8,
                  border: `1px solid ${mcColors.border}`,
                  background: "rgba(0,0,0,0.2)",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{m.label}</div>
                  <div style={{ fontSize: 11, color: mcColors.textDim }}>
                    {m.params_b}B · {m.quant} · needs ~{m.min_gb} GB
                  </div>
                </div>
                <span style={{ fontSize: 12, fontWeight: 700, color: VERDICT_COLOR[m.verdict] || mcColors.textMuted }}>
                  {Math.round(m.fit_score * 100)}% · {m.verdict}
                </span>
                <button
                  type="button"
                  disabled={!m.fits}
                  onClick={() => void requestServe(m.id)}
                  style={{ ...mcButtonSecondaryStyle, fontSize: 12, opacity: m.fits ? 1 : 0.4 }}
                  title={m.fits ? "Record a governed serve request" : "Below recommended hardware fit"}
                >
                  Serve…
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
