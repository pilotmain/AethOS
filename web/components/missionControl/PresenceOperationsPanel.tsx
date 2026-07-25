"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchAttentionQuality,
  fetchIntelligentRecommendations,
  fetchPresenceAttention,
  fetchPresenceClusters,
  fetchPresenceFeed,
  fetchPresenceFocus,
  fetchPresenceIncidents,
  fetchPresenceMemory,
  fetchPresenceState,
  fetchPresenceTimeline,
  fetchPresenceWatchers,
  registerWatcher,
  runPresenceCycle,
  type AttentionQuality,
  type PresenceCluster,
  type PresenceFeedEvent,
  type PresenceRecommendation,
  type PresenceState,
} from "@/lib/missionControl/presenceApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const priorityColor = (p?: string) => {
  const key = (p || "").toLowerCase();
  if (key === "critical") return mcColors.red;
  if (key === "urgent") return mcColors.amber;
  if (key === "elevated") return mcColors.cyan;
  if (key === "notice") return mcColors.textMuted;
  return mcColors.textDim;
};

const titles: Record<string, string> = {
  "presence-feed": "Live Feed",
  "presence-attention": "Attention Center",
  "presence-timeline": "Presence Timeline",
  "presence-focus": "Active Focus",
  "presence-collaboration": "Collaboration Sessions",
  "presence-recommendations": "Recommendation Queue",
  "presence-watch": "Watch Mode",
  "presence-memory": "Operational Memory",
};

function FeedCard({ item }: { item: PresenceFeedEvent }) {
  return (
    <div style={cardStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontWeight: 600 }}>{item.summary}</span>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {item.deduplicated ? (
            <span style={{ fontSize: 10, color: mcColors.cyan, border: `1px solid ${mcColors.cyan}`, borderRadius: 4, padding: "1px 5px" }}>
              deduped ×{item.dedupe_count ?? 2}
            </span>
          ) : null}
          <span style={{ fontSize: 11, color: priorityColor(item.priority) }}>
            {item.priority?.toUpperCase() || item.severity?.toUpperCase()}
          </span>
        </div>
      </div>
      <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
        {item.source}
        {item.context_weight != null ? ` · relevance ${item.context_weight}` : ""}
        {item.attention_score != null ? ` · score ${item.attention_score}` : ""}
        {item.confidence != null ? ` · conf ${item.confidence}` : ""}
      </div>
      {item.attention_reason ? (
        <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>{item.attention_reason}</div>
      ) : null}
    </div>
  );
}

function ClusterCard({ cluster }: { cluster: PresenceCluster }) {
  return (
    <div style={{ ...cardStyle, borderLeft: `3px solid ${mcColors.cyan}` }}>
      <div style={{ fontWeight: 600 }}>{cluster.title}</div>
      <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
        {cluster.event_count} signals · confidence {cluster.confidence ?? "—"} · {cluster.theme}
      </div>
      {cluster.related_systems?.length ? (
        <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>
          Systems: {cluster.related_systems.join(", ")}
        </div>
      ) : null}
    </div>
  );
}

function RecommendationCard({ rec }: { rec: PresenceRecommendation }) {
  return (
    <div style={cardStyle}>
      <div style={{ fontWeight: 600 }}>{rec.title}</div>
      <div style={{ marginTop: 6 }}>{rec.suggested_action}</div>
      <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 6 }}>
        Confidence {rec.confidence ?? "—"} · {rec.severity ?? "medium"} · approval required
      </div>
      {rec.operator_rationale ? (
        <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>Rationale: {rec.operator_rationale}</div>
      ) : null}
      {rec.governance_statement ? (
        <div style={{ fontSize: 11, color: mcColors.amber, marginTop: 4 }}>{rec.governance_statement}</div>
      ) : null}
    </div>
  );
}

function QualitySummary({ quality }: { quality?: AttentionQuality }) {
  if (!quality) return null;
  const dist = quality.priority_distribution ?? {};
  return (
    <div style={{ ...cardStyle, marginBottom: 16, fontSize: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>Attention quality</div>
      <div style={{ color: mcColors.textMuted }}>
        High-signal: {quality.high_signal_count ?? 0} · Passive: {quality.passive_count ?? 0} · Inflation ratio:{" "}
        {quality.urgency_inflation_ratio ?? 0}
      </div>
      <div style={{ marginTop: 4, color: mcColors.textDim }}>
        {Object.entries(dist)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ")}
      </div>
    </div>
  );
}

export function PresenceOperationsPanel({ view }: Props) {
  const [state, setState] = useState<PresenceState | null>(null);
  const [clusters, setClusters] = useState<PresenceCluster[]>([]);
  const [incidents, setIncidents] = useState<PresenceCluster[]>([]);
  const [recommendations, setRecommendations] = useState<PresenceRecommendation[]>([]);
  const [attentionQuality, setAttentionQuality] = useState<AttentionQuality | undefined>();
  const [timeline, setTimeline] = useState<{ timeline_id?: string; entries?: unknown[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "presence-attention") {
        const att = await fetchPresenceAttention();
        setState({ ok: true, attention: att.attention });
        setAttentionQuality(att.attention_quality);
        const inc = await fetchPresenceIncidents();
        setIncidents(inc.incidents ?? []);
      } else if (view === "presence-feed") {
        const feed = await fetchPresenceFeed();
        setState({ ok: true, feed: feed.feed, attention: feed.attention });
        setClusters(feed.clusters ?? []);
        setAttentionQuality(feed.attention_quality);
      } else if (view === "presence-recommendations") {
        const recs = await fetchIntelligentRecommendations();
        setRecommendations(recs.recommendations ?? []);
      } else if (view === "presence-timeline") {
        const tl = await fetchPresenceTimeline();
        setTimeline(tl.timeline ?? null);
        const inc = await fetchPresenceIncidents();
        setIncidents(inc.incidents ?? []);
      } else if (view === "presence-focus") {
        const f = await fetchPresenceFocus();
        setState({ ok: true, focus: f.focus ?? undefined });
      } else if (view === "presence-watch") {
        const w = await fetchPresenceWatchers();
        setState({ ok: true, watchers: w.watchers });
      } else if (view === "presence-memory") {
        const m = await fetchPresenceMemory();
        setState({ ok: true, memory: m.memory });
      } else {
        const s = await fetchPresenceState();
        setState(s);
        setClusters(s.clusters ?? []);
        setIncidents(s.incidents ?? []);
        setRecommendations(s.recommendations ?? []);
        setAttentionQuality(s.attention_quality);
      }
      if (view === "presence-attention") {
        const q = await fetchAttentionQuality();
        setAttentionQuality(q.attention_quality);
      }
      if (view !== "presence-recommendations" && view !== "presence-feed" && view !== "presence-attention") {
        const cl = await fetchPresenceClusters();
        if (cl.clusters?.length) setClusters(cl.clusters);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load presence state");
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  const onCycle = async () => {
    setBusy(true);
    try {
      await runPresenceCycle();
      await load();
    } finally {
      setBusy(false);
    }
  };

  const onWatch = async (target: string) => {
    setBusy(true);
    try {
      await registerWatcher(target);
      await load();
    } finally {
      setBusy(false);
    }
  };

  const feed = state?.feed ?? state?.attention ?? [];

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{titles[view] ?? "Operational Presence"}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            High-signal operational collaborator — deduplicated, contextual, never self-authorizing.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" disabled={busy} onClick={onCycle} style={mcButtonSecondaryStyle}>
            Run cycle
          </button>
          <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
            Refresh
          </button>
        </div>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {(view === "presence-feed" || view === "presence-attention") && (
        <div style={{ marginTop: 16 }}>
          <QualitySummary quality={attentionQuality} />
          {view === "presence-attention" && incidents.length > 0 ? (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Grouped incidents</div>
              {incidents.map((c) => (
                <ClusterCard key={c.cluster_id} cluster={c} />
              ))}
            </>
          ) : null}
          {clusters.length > 0 && view === "presence-feed" ? (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Signal clusters</div>
              {clusters.slice(0, 4).map((c) => (
                <ClusterCard key={c.cluster_id} cluster={c} />
              ))}
            </>
          ) : null}
          {feed.length === 0 ? (
            <p style={{ color: mcColors.textMuted }}>No feed events yet. Run a presence cycle or wait for scheduler.</p>
          ) : (
            feed.map((item, i) => <FeedCard key={item.event_id || i} item={item} />)
          )}
        </div>
      )}

      {view === "presence-timeline" && (
        <div style={{ marginTop: 16 }}>
          {incidents.length > 0 ? (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Incident ribbons</div>
              {incidents.map((c) => (
                <ClusterCard key={c.cluster_id} cluster={c} />
              ))}
            </>
          ) : null}
          {timeline ? (
            <>
              <div style={cardStyle}>
                Timeline: {timeline.timeline_id} · {timeline.entries?.length ?? 0} entries
              </div>
              {(timeline.entries ?? []).slice(0, 12).map((e, i) => (
                <div key={i} style={{ ...cardStyle, fontSize: 12 }}>
                  <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: mcColors.textMuted }}>{JSON.stringify(e, null, 2)}</pre>
                </div>
              ))}
            </>
          ) : (
            <p style={{ color: mcColors.textMuted }}>No timeline generated yet.</p>
          )}
        </div>
      )}

      {view === "presence-focus" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>Focus mode: {state?.focus?.mode || "none"}</div>
            <div style={{ color: mcColors.textMuted, marginTop: 4 }}>{state?.focus?.investigation || "No active investigation"}</div>
            <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 8 }}>
              Focus shapes signal weighting — deployment_debug elevates Railway/GitHub signals and suppresses substrate noise.
            </div>
          </div>
        </div>
      )}

      {view === "presence-watch" && (
        <div style={{ marginTop: 16 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
            {["railway_deployment", "github_workflow", "dependency_risk", "browser_anomalies"].map((t) => (
              <button key={t} type="button" disabled={busy} onClick={() => onWatch(t)} style={{ ...mcButtonSecondaryStyle, fontSize: 11 }}>
                Watch {t.replace(/_/g, " ")}
              </button>
            ))}
          </div>
          {(state?.watchers ?? []).map((w) => (
            <div key={w.watcher_id} style={cardStyle}>
              {w.target} · {w.status}
            </div>
          ))}
        </div>
      )}

      {view === "presence-memory" && state?.memory && (
        <div style={{ marginTop: 16 }}>
          <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>{JSON.stringify(state.memory, null, 2)}</pre>
        </div>
      )}

      {view === "presence-recommendations" && (
        <div style={{ marginTop: 16 }}>
          {recommendations.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No contextual recommendations from current signal clusters.</p>
          ) : (
            recommendations.map((rec) => <RecommendationCard key={rec.recommendation_id} rec={rec} />)
          )}
        </div>
      )}

      {view === "presence-collaboration" && (
        <div style={{ marginTop: 16 }}>
          <p style={{ color: mcColors.textMuted }}>Collaboration sessions track operator focus and investigations.</p>
          <div style={cardStyle}>Focus: {state?.focus?.mode || "—"}</div>
        </div>
      )}
    </section>
  );
}
