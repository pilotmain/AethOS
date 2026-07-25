// SPDX-License-Identifier: Apache-2.0
// Multi-Model Arbiter panel — Mission Control native. Dispatches one prompt to
// every configured model in parallel, runs a governed blind peer-critique round,
// and reports the consensus verdict. Read-only analysis.

"use client";

import { useEffect, useRef, useState } from "react";

import {
  fetchArbiterConsensus,
  fetchArbiterSessions,
  fetchArbiterStatus,
  runArbiterSession,
  type ArbiterSessionResult,
  type ArbiterStatus,
} from "@/lib/missionControl/phase4Api";
import { setRuntimeConfig } from "@/lib/missionControl/runtimeConfigApi";
import { classifyModelError, toneColor } from "@/lib/missionControl/modelErrorClassifier";
import {
  mcButtonPrimaryStyle,
  mcButtonSecondaryStyle,
  mcColors,
  mcGradientTextStyle,
  mcPanelSectionStyle,
} from "@/lib/missionControl/layout";

export function ArbiterPanel({ initialSessionId }: { initialSessionId?: string | null } = {}) {
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState<ArbiterStatus | null>(null);
  const [result, setResult] = useState<ArbiterSessionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [savingPool, setSavingPool] = useState(false);
  const [poolNotice, setPoolNotice] = useState<string | null>(null);
  const [debateRounds, setDebateRounds] = useState(0);
  const resultRef = useRef<HTMLDivElement | null>(null);

  // When a result loads (fresh run OR clicking a past session), scroll it into view —
  // otherwise it renders above the list and looks like nothing happened.
  useEffect(() => {
    if (result) resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [result]);

  function refreshStatus() {
    void fetchArbiterStatus().then((s) => {
      setStatus(s);
      if (s) setSelected(new Set(s.pool.map((m) => `${m.provider}:${m.model_id}`)));
    });
  }

  useEffect(() => {
    refreshStatus();
    void fetchArbiterSessions(5).then((d) => setHistory(d.sessions ?? []));
  }, []);

  // Deep link: when opened from Audit Logs with a specific session, load its results.
  useEffect(() => {
    if (initialSessionId) void openSession(initialSessionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSessionId]);

  function toggleModel(poolId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(poolId)) next.delete(poolId);
      else next.add(poolId);
      return next;
    });
  }

  async function savePool() {
    setSavingPool(true);
    setPoolNotice(null);
    setError(null);
    try {
      await setRuntimeConfig("ARBITER_MODEL_POOL", Array.from(selected).join(","));
      setPoolNotice("Model pool saved.");
      refreshStatus();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save model pool");
    } finally {
      setSavingPool(false);
    }
  }

  async function run() {
    const q = prompt.trim();
    if (q.length < 8) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const r = await runArbiterSession(q, "mission-control", debateRounds);
      setResult(r);
      void fetchArbiterSessions(5).then((d) => setHistory(d.sessions ?? []));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Arbiter session failed");
    } finally {
      setBusy(false);
    }
  }

  async function openSession(sessionId: string) {
    if (!sessionId) return;
    setError(null);
    try {
      const r = await fetchArbiterConsensus(sessionId);
      if (r) setResult(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not load session");
    }
  }

  const poolReady = Boolean(status?.enabled && status?.pool_valid);

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 22, fontWeight: 750, letterSpacing: "-0.02em", width: "fit-content", ...mcGradientTextStyle }}>
        Multi-model arbiter
      </h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 560 }}>
        Dispatch a prompt to all configured models in parallel. Each model critiques the others
        (blind by default). Consensus is declared when{" "}
        {status ? `${Math.round((status.config.consensus_threshold ?? 0.6) * 100)}%` : "60%"} of
        models agree on the best response.
      </p>

      {status && (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "4px 10px",
            borderRadius: 20,
            fontSize: 11,
            fontWeight: 600,
            background: poolReady ? "rgba(5,150,105,0.15)" : "rgba(239,68,68,0.12)",
            border: `1px solid ${poolReady ? "#059669" : "#ef4444"}`,
            color: poolReady ? "#6ee7b7" : "#fca5a5",
            marginBottom: 16,
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: poolReady ? "#10b981" : "#ef4444",
            }}
          />
          {poolReady
            ? `${status.pool.length} models configured · threshold ${Math.round(status.config.consensus_threshold * 100)}%`
            : (status.pool_errors[0] ?? "Arbiter not configured")}
        </div>
      )}

      {status && !poolReady && status.pool_errors.length > 0 && (
        <div
          style={{
            marginBottom: 16,
            padding: "10px 14px",
            borderRadius: 6,
            background: "rgba(127,29,29,0.25)",
            border: "1px solid rgba(239,68,68,0.3)",
            fontSize: 12,
            color: "#fca5a5",
          }}
        >
          <strong>Setup required:</strong>
          <ul style={{ margin: "6px 0 0 0", paddingLeft: 16 }}>
            {status.pool_errors.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
          <div style={{ marginTop: 8, color: mcColors.textMuted }}>
            Enable the arbiter in <strong>Settings</strong>, connect models in{" "}
            <strong>Connections</strong>, then select at least 2 below — no <code>.env</code> editing
            needed.
          </div>
        </div>
      )}

      {status && status.available_models.length > 0 && (
        <div
          style={{
            marginBottom: 16,
            padding: "12px 14px",
            borderRadius: 8,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: "rgba(0,0,0,0.2)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 8,
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 600, color: mcColors.text }}>
              Model pool ({selected.size} selected)
            </span>
            <button
              type="button"
              onClick={savePool}
              disabled={savingPool}
              style={mcButtonSecondaryStyle}
            >
              {savingPool ? "Saving…" : "Save selection"}
            </button>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {status.available_models.map((m) => {
              const checked = selected.has(m.pool_id);
              return (
                <label
                  key={m.pool_id}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "4px 10px",
                    borderRadius: 6,
                    fontSize: 11,
                    cursor: "pointer",
                    background: checked ? "rgba(8,145,178,0.18)" : "rgba(0,0,0,0.25)",
                    border: `1px solid ${checked ? mcColors.cyan : mcColors.borderSubtle}`,
                    color: checked ? mcColors.text : mcColors.textMuted,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleModel(m.pool_id)}
                    style={{ accentColor: "var(--aethos-accent)" }}
                  />
                  {m.label}
                </label>
              );
            })}
          </div>
          {poolNotice ? (
            <div style={{ marginTop: 8, fontSize: 11, color: mcColors.green }}>{poolNotice}</div>
          ) : null}
          {status.pool_source === "connected_models_default" && (
            <div style={{ marginTop: 8, fontSize: 11, color: mcColors.textDim }}>
              No explicit selection — using all connected models by default.
            </div>
          )}
        </div>
      )}

      {status?.pool && status.pool.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
          {status.pool.map((m) => (
            <span
              key={`${m.provider}:${m.model_id}`}
              style={{
                padding: "3px 8px",
                borderRadius: 4,
                fontSize: 11,
                background: "rgba(8,145,178,0.12)",
                border: "1px solid rgba(8,145,178,0.25)",
                color: mcColors.textMuted,
              }}
            >
              {m.label}
            </span>
          ))}
        </div>
      )}

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        disabled={busy || !poolReady}
        placeholder={
          poolReady
            ? "Enter a prompt to compare across all models…"
            : "Configure the model pool to enable the arbiter."
        }
        rows={4}
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: 8,
          border: `1px solid ${mcColors.borderSubtle}`,
          background: "rgba(0,0,0,0.35)",
          color: mcColors.text,
          fontSize: 13,
          resize: "vertical",
          boxSizing: "border-box",
          opacity: poolReady ? 1 : 0.5,
        }}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12, flexWrap: "wrap" }}>
        <label style={{ fontSize: 12, color: mcColors.textMuted, display: "inline-flex", alignItems: "center", gap: 6 }}>
          Debate rounds
          <select
            value={debateRounds}
            onChange={(e) => setDebateRounds(Number(e.target.value))}
            disabled={busy || !poolReady}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              background: "rgba(0,0,0,0.35)",
              color: mcColors.text,
              border: `1px solid ${mcColors.borderSubtle}`,
              fontSize: 12,
            }}
          >
            <option value={0}>0 — single pass (fastest)</option>
            <option value={1}>1 round</option>
            <option value={2}>2 rounds</option>
            <option value={3}>3 rounds (deepest)</option>
          </select>
        </label>
        {debateRounds > 0 && (
          <span style={{ fontSize: 11, color: mcColors.textDim }}>
            Models revise &amp; re-critique each round — more thorough, more API spend.
          </span>
        )}
      </div>

      <button
        type="button"
        onClick={run}
        disabled={busy || !poolReady || prompt.trim().length < 8}
        style={{ ...mcButtonPrimaryStyle, marginTop: 10 }}
      >
        {busy
          ? debateRounds > 0
            ? "Running debate…"
            : "Running arbiter…"
          : debateRounds > 0
            ? `Run ${debateRounds}-round debate`
            : "Run arbiter"}
      </button>

      {error && (
        <div
          style={{
            marginTop: 12,
            padding: "10px 14px",
            borderRadius: 6,
            background: "rgba(127,29,29,0.25)",
            border: "1px solid rgba(239,68,68,0.3)",
            fontSize: 12,
            color: "#fca5a5",
          }}
        >
          {error}
        </div>
      )}

      {result && (
        <div ref={resultRef} style={{ marginTop: 20, scrollMarginTop: 12 }}>
          {result.consensus && (
            <div
              style={{
                padding: "14px 16px",
                borderRadius: 8,
                background: result.consensus.reached ? "rgba(6,78,59,0.35)" : "rgba(28,25,23,0.5)",
                border: `1px solid ${result.consensus.reached ? "#059669" : "#57534e"}`,
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 13,
                  color: result.consensus.reached ? "#6ee7b7" : "#a8a29e",
                  marginBottom: 6,
                }}
              >
                {result.consensus.reached ? "✓ Consensus" : "⚠ No consensus"}
                {"  ·  "}
                {Math.round(result.consensus.agreement_score * 100)}% agreement
                {result.consensus.winning_model && (
                  <>
                    {"  ·  Winner: "}
                    <strong>{result.consensus.winning_model}</strong>
                  </>
                )}
              </div>
              <div style={{ fontSize: 12, color: mcColors.textMuted }}>
                {result.consensus.summary}
              </div>
              {result.consensus.winning_text && (
                <details style={{ marginTop: 10 }}>
                  <summary style={{ cursor: "pointer", fontSize: 12, color: mcColors.textMuted }}>
                    View winning response
                  </summary>
                  <pre
                    style={{
                      marginTop: 8,
                      whiteSpace: "pre-wrap",
                      fontSize: 12,
                      color: mcColors.text,
                      background: "rgba(0,0,0,0.4)",
                      padding: "10px 12px",
                      borderRadius: 6,
                      maxHeight: 300,
                      overflowY: "auto",
                    }}
                  >
                    {result.consensus.winning_text}
                  </pre>
                </details>
              )}
            </div>
          )}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: 10,
            }}
          >
            {result.responses.map((resp) => {
              const isWinner = resp.model_label === result.consensus?.winning_model;
              return (
                <div
                  key={resp.response_id}
                  style={{
                    padding: "12px 14px",
                    borderRadius: 8,
                    background: isWinner ? "rgba(6,78,59,0.2)" : "rgba(15,23,42,0.6)",
                    border: `1px solid ${
                      resp.error
                        ? "rgba(239,68,68,0.3)"
                        : isWinner
                          ? "#059669"
                          : mcColors.borderSubtle
                    }`,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 6,
                    }}
                  >
                    <span style={{ fontWeight: 600, fontSize: 12, color: mcColors.text }}>
                      {resp.model_label}
                      {isWinner && (
                        <span style={{ marginLeft: 6, color: "#34d399", fontSize: 10 }}>
                          ✓ winner
                        </span>
                      )}
                    </span>
                    <span style={{ fontSize: 10, color: mcColors.textMuted }}>
                      {resp.latency_ms ? `${resp.latency_ms}ms` : "—"}
                    </span>
                  </div>
                  {resp.error ? (
                    (() => {
                      const failure = classifyModelError(resp.error);
                      return (
                        <div style={{ fontSize: 11, color: toneColor(failure.tone) }}>
                          {failure.hint}
                          {failure.raw && failure.raw !== failure.hint ? (
                            <details style={{ marginTop: 4 }}>
                              <summary style={{ cursor: "pointer", color: mcColors.textDim }}>
                                Details
                              </summary>
                              <span style={{ color: mcColors.textMuted }}>{failure.raw}</span>
                            </details>
                          ) : null}
                        </div>
                      );
                    })()
                  ) : (
                    <details>
                      <summary style={{ cursor: "pointer", fontSize: 11, color: mcColors.textMuted, marginBottom: 4 }}>
                        {(resp.text_preview ?? "(no preview)").slice(0, 90)}
                        {(resp.text_preview ?? "").length > 90 ? "… (click to expand)" : ""}
                      </summary>
                      <div style={{ fontSize: 11, color: mcColors.text, lineHeight: 1.6, whiteSpace: "pre-wrap", marginTop: 4 }}>
                        {resp.text_preview ?? "(no preview)"}
                      </div>
                    </details>
                  )}
                </div>
              );
            })}
          </div>

          {result.critiques && result.critiques.length > 0 && (
            <details style={{ marginTop: 16 }} open>
              <summary
                style={{ cursor: "pointer", fontSize: 13, fontWeight: 600, color: mcColors.text }}
              >
                Judgment scorecard — why this score ({result.critiques.length} critiques)
              </summary>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 10 }}>
                {result.critiques.map((c, i) => (
                  <div
                    key={`${c.critic}-${c.target}-${i}`}
                    style={{
                      padding: "10px 12px",
                      borderRadius: 8,
                      background: "rgba(15,23,42,0.55)",
                      border: `1px solid ${c.recommended ? "rgba(5,150,105,0.4)" : mcColors.borderSubtle}`,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                      <span style={{ color: mcColors.text }}>
                        <strong>{c.critic}</strong>
                        <span style={{ color: mcColors.textDim }}> → </span>
                        <strong>{c.target}</strong>
                      </span>
                      <span style={{ color: c.recommended ? "#6ee7b7" : mcColors.textMuted }}>
                        {Math.round(c.overall_score * 100)}% {c.recommended ? "· ✓ recommends" : "· not recommended"}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: mcColors.textMuted, lineHeight: 1.5 }}>
                      {c.critique || "(no written critique)"}
                    </div>
                    <div style={{ fontSize: 10, color: mcColors.textDim, marginTop: 4 }}>
                      accuracy {Math.round(c.accuracy_score * 100)}% · completeness{" "}
                      {Math.round(c.completeness_score * 100)}% · reasoning {Math.round(c.reasoning_score * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            </details>
          )}

          {result.debate_rounds && result.debate_rounds.length > 0 && (
            <details style={{ marginTop: 16 }}>
              <summary
                style={{ cursor: "pointer", fontSize: 13, fontWeight: 600, color: mcColors.text }}
              >
                Debate timeline — {result.debate_rounds.length} revise/re-critique round
                {result.debate_rounds.length > 1 ? "s" : ""}
              </summary>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
                {result.debate_rounds.map((rd) => (
                  <div
                    key={rd.round}
                    style={{
                      padding: "10px 12px",
                      borderRadius: 8,
                      background: "rgba(0,0,0,0.25)",
                      border: `1px solid ${mcColors.borderSubtle}`,
                    }}
                  >
                    <div style={{ fontSize: 12, fontWeight: 600, color: mcColors.text, marginBottom: 6 }}>
                      Round {rd.round} · {Math.round(rd.agreement_score * 100)}% agreement
                      {rd.winning_model ? ` · leading: ${rd.winning_model}` : ""}
                    </div>
                    {rd.answers.map((a, j) => (
                      <details key={`${rd.round}-${a.model_label}-${j}`} style={{ marginTop: 4 }}>
                        <summary style={{ cursor: "pointer", fontSize: 11, color: mcColors.textMuted }}>
                          {a.model_label} — revised answer
                        </summary>
                        <pre
                          style={{
                            marginTop: 4,
                            whiteSpace: "pre-wrap",
                            fontSize: 11,
                            color: mcColors.textMuted,
                            background: "rgba(0,0,0,0.4)",
                            padding: "8px 10px",
                            borderRadius: 6,
                            maxHeight: 200,
                            overflowY: "auto",
                          }}
                        >
                          {a.text_preview}
                        </pre>
                      </details>
                    ))}
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h3
            style={{ margin: "0 0 10px", fontSize: 13, fontWeight: 600, color: mcColors.textMuted }}
          >
            Recent sessions <span style={{ color: mcColors.textDim, fontWeight: 400 }}>(click to view results &amp; judgment)</span>
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {history.map((s, i) => {
              const consensus = s.consensus as Record<string, unknown> | null;
              const sid = String(s.session_id ?? "");
              return (
                <button
                  type="button"
                  key={sid || i}
                  onClick={() => void openSession(sid)}
                  disabled={!sid}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px 12px",
                    borderRadius: 6,
                    background: "rgba(15,23,42,0.5)",
                    border: `1px solid ${mcColors.borderSubtle}`,
                    fontSize: 11,
                    textAlign: "left",
                    cursor: sid ? "pointer" : "default",
                    color: "inherit",
                    width: "100%",
                  }}
                >
                  <span
                    style={{
                      color: mcColors.text,
                      flex: 1,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {String(s.prompt_preview ?? "").slice(0, 60)}…
                  </span>
                  <span
                    style={{
                      marginLeft: 12,
                      color: consensus?.reached ? "#6ee7b7" : "#a8a29e",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {consensus?.reached
                      ? `✓ ${Math.round((Number(consensus.agreement_score) || 0) * 100)}%`
                      : String(s.status ?? "—")}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
