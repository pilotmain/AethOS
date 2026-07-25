"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";

import { IntelligenceFindingCard } from "@/components/missionControl/IntelligenceFindingCard";
import { ConnectionsHealthOverview } from "@/components/settings/ProviderCatalog/ConnectionsHealthOverview";
import { computeCognitiveSanctuary } from "@/lib/missionControl/cognitiveSanctuary";
import {
  buildFocusCanvasState,
  contentForDepth,
  depthLabel,
  type ProgressiveDepth,
} from "@/lib/missionControl/focusCanvas";
import type { ConnectionsCatalogResponse } from "@/lib/missionControl/connectionsCatalog";
import { fetchCompanionQuality, fetchPartnerBrief } from "@/lib/missionControl/humanApi";
import { rhythmClassNames } from "@/lib/missionControl/livingRhythm";
import { buildOperationalNarrative } from "@/lib/missionControl/operationalStorytelling";
import { assessQuietIntelligence, shouldShowDepthExpand } from "@/lib/missionControl/quietIntelligence";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";
import {
  prioritizeSurfaces,
  shouldShowConnectionHealth,
  shouldShowMetricStrip,
} from "@/lib/missionControl/surfacePrioritization";
import {
  attentionChipStyle,
  calmTypography,
  primaryFocusStyle,
  spatialLayerStyle,
} from "@/lib/missionControl/spatialHierarchy";
import { mcButtonSecondaryStyle, mcColors } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  catalog: ConnectionsCatalogResponse | null;
  onNavigate: (view: MissionControlView) => void;
  mode?: MissionControlMode;
  context?: NavigationContext;
  quietMode?: boolean;
  focusMode?: boolean;
};

export function OperationalOverviewPanel({
  catalog,
  onNavigate,
  mode = "operator",
  context = {},
  quietMode = false,
  focusMode = false,
}: Props) {
  const [brief, setBrief] = useState<Record<string, unknown> | null>(null);
  const [quality, setQuality] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [depth, setDepth] = useState<ProgressiveDepth>(0);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [b, q] = await Promise.all([fetchPartnerBrief(), fetchCompanionQuality()]);
      setBrief(b);
      setQuality(q);
      setDepth(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load operational brief");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const focus = useMemo(() => buildFocusCanvasState(brief, quality), [brief, quality]);
  const metrics = (quality?.metrics as Record<string, number>) ?? {};
  const recentlyResolved = focus.confidence >= 0.82 && !context.hasAnomalies;

  const opsSanctuary = useMemo(
    () =>
      computeCognitiveSanctuary(context, {
        mode,
        quietMode,
        focusMode,
        confidence: focus.confidence,
        recentlyResolved,
        priorityIssue: focus.priorityIssue,
      }),
    [context, mode, quietMode, focusMode, focus.confidence, focus.priorityIssue, recentlyResolved],
  );

  const { ops: opsConsciousness, sanctuary, flowContinuity, emotionalResilience, cognitiveSustainability, sanctuaryAttention } = opsSanctuary;
  const { cognition, consciousness, flowProtection, harmony, cognitiveErgonomics } = opsConsciousness;
  const { partnership, ambientFlow, guidance, calmComputing, ergonomics } = cognition;
  const intelligence = partnership.intelligence;
  const { presence, flow, assistance, trustAtmosphere, emotionalStability } = intelligence;
  const { environment, cognitive, invisible, emotionalTrust } = presence;
  const { partnership: partnerState, trustPresence, humanRealism } = partnership;

  const quiet = useMemo(
    () =>
      assessQuietIntelligence({
        quietMode,
        focusMode,
        confidence: focus.confidence,
        loading,
      }),
    [quietMode, focusMode, focus.confidence, loading],
  );

  const narrative = useMemo(
    () =>
      buildOperationalNarrative({
        priorityIssue: focus.priorityIssue,
        confidence: focus.confidence,
        confidenceLabel: focus.confidenceLabel,
        replayDegraded: context.replayIntegrityDegraded,
        anomalyCount: context.hasAnomalies ? 2 : 0,
        preflightActive: context.hasActivePreflights,
        recentlyResolved,
        pendingRecommendations: context.pendingRecommendations,
        replayDetail: focus.replayDetail,
        reasoning: focus.reasoning,
        dominantThought: sanctuary.partnerHeadline ?? cognitiveSustainability.partnerHeadline ?? consciousness.companionHeadline ?? cognitiveErgonomics.companionPhrase ?? guidance.narrativeHint ?? partnerState.companionHeadline ?? assistance.passiveGuidance ?? presence.dominantThought,
        emotionalTrust,
        humanRealism,
        serenity: partnership.serenity,
        calmComputing,
        ergonomics,
        harmony,
        cognitiveErgonomics,
        emotionalResilience,
        cognitiveSustainability,
        compression: {
          replayDegraded: context.replayIntegrityDegraded,
          replayAlertCount: context.replayIntegrityDegraded ? 6 : 0,
          telemetryAlertCount: context.hasAnomalies ? 3 : 0,
          recommendationCount: context.pendingRecommendations,
          recoveryNotices: recentlyResolved ? 1 : 0,
          confidenceChanges: recentlyResolved ? 1 : 0,
          confidenceWarnings: context.replayIntegrityDegraded ? 2 : 0,
        },
      }),
    [focus, context, recentlyResolved, presence.dominantThought, sanctuary.partnerHeadline, cognitiveSustainability.partnerHeadline, consciousness.companionHeadline, cognitiveErgonomics.companionPhrase, partnerState.companionHeadline, assistance.passiveGuidance, guidance.narrativeHint, emotionalTrust, humanRealism, partnership.serenity, calmComputing, ergonomics, harmony, cognitiveErgonomics, emotionalResilience, cognitiveSustainability],
  );

  const surfaces = useMemo(
    () => prioritizeSurfaces(mode, context).slice(0, flowContinuity.maxSurfaces),
    [mode, context, flowContinuity.maxSurfaces],
  );

  const nextDepthLabel = depthLabel(depth);
  const visibleContent = contentForDepth(focus, depth);
  const showMetrics =
    shouldShowMetricStrip(mode, quietMode) &&
    !quiet.suppressSecondaryMetrics &&
    !cognitive.compressLowConfidenceTelemetry &&
    !flowProtection.interruptionPrevented &&
    !environment.pacing.suppressUrgencyStacking;
  const showHealth =
    shouldShowConnectionHealth(mode, context) &&
    !invisible.suppressLowValueSurfaces &&
    !flowProtection.interruptionPrevented;
  const showExpand = shouldShowDepthExpand(depth, quiet, Boolean(nextDepthLabel));
  const rhythmClasses = rhythmClassNames(environment.rhythm);
  const silenceNote = guidance.environmentalCue ?? assistance.operationalAnticipation ?? invisible.silenceNote ?? quiet.silenceReason;
  const headline = narrative.structuredFindings[0]?.finding ?? narrative.dominantNarrative ?? narrative.companionHeadline;
  const companionCommentary = [
    emotionalResilience.operationalReassurance,
    harmony.harmonyPhrase,
    calmComputing.calmPhrase,
    trustPresence.operationalSteadiness,
    narrative.recoveryStory,
    narrative.primaryStory !== headline ? narrative.primaryStory : null,
    humanRealism.supportiveTone,
    emotionalStability.supportivePhrase,
    cognitiveErgonomics.calmPhrasing,
    silenceNote,
    opsSanctuary.sanctuaryWhisper,
  ].filter(Boolean);
  const showWhisper = !flowContinuity.suppressPeripheralSignals && opsSanctuary.atmosphereLevel !== "invisible";

  return (
    <div
      className={`mc-focus-canvas-root mc-fade-in mc-living-space mc-sanctuary-canvas ${opsSanctuary.sanctuaryClassName} ${rhythmClasses}`}
      data-mc-ambient={environment.mood}
      data-mc-atmosphere={environment.atmosphere}
      data-mc-cognitive={cognitive.loadLevel}
      data-mc-flow={ambientFlow.flowState}
      data-mc-consciousness={consciousness.consciousnessState}
      data-mc-sanctuary={sanctuary.sanctuaryState}
      data-mc-attention={sanctuaryAttention}
      data-mc-whisper={opsSanctuary.atmosphereLevel}
      data-mc-serenity={opsSanctuary.sanctuaryImmersion ? "true" : undefined}
      style={environment.cssVars as CSSProperties}
    >
      {showWhisper ? (
        <p
          className={`mc-presence-whisper mc-trust-whisper mc-sanctuary-whisper ${opsSanctuary.atmosphereLevel === "whisper" || opsSanctuary.atmosphereLevel === "atmospheric" ? "mc-whisper-passive" : ""}`}
          style={{ ...calmTypography.meta, marginBottom: 44 }}
        >
          {opsSanctuary.sanctuaryWhisper}
        </p>
      ) : null}

      <section
        className={`mc-focus-primary mc-living-canvas ${consciousness.immersionPreservation || opsSanctuary.sanctuaryImmersion ? "mc-investigation-expanded mc-single-thought mc-deep-sanctuary-immersion-canvas" : ""}`}
        style={primaryFocusStyle(
          environment.focusOutline,
          environment.cssVars["--mc-atmosphere-depth"],
        )}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 32 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p className="mc-signal-whisper" style={calmTypography.sectionLabel}>
              Operational intelligence
            </p>
            <h2 className="mc-focus-headline mc-signal-dominant" style={{ ...calmTypography.focusTitle, marginTop: 24 }}>{headline}</h2>
            <p className="mc-signal-reassurance" style={{ ...calmTypography.focusLead, marginTop: 16, color: mcColors.textMuted }}>
              Evidence-first findings — interpretation and recommendations separated for auditability.
            </p>
          </div>
          {!flowContinuity.suppressPeripheralSignals && !flow.suppressSecondaryDomains && !cognitive.suppressSecondaryChrome ? (
            <button type="button" className="mc-calm-button mc-luxury-button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
              Refresh
            </button>
          ) : null}
        </div>

        {!environment.pacing.suppressUrgencyStacking &&
        !emotionalTrust.suppressOverclaiming &&
        sanctuaryAttention !== "invisible" &&
        sanctuaryAttention !== "whisper" &&
        sanctuaryAttention !== "atmospheric" &&
        !flowContinuity.interruptionShielding ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 24 }}>
            <span style={attentionChipStyle(sanctuaryAttention)}>
              Confidence · {focus.confidence.toFixed(2)} ({focus.confidenceLabel})
            </span>
            {showMetrics ? (
              <span style={attentionChipStyle("silent")}>Trust · {metrics.trust_retention ?? "—"}</span>
            ) : null}
          </div>
        ) : null}

        <div style={{ marginTop: 32, maxWidth: 860 }}>
          {loading ? (
            <p style={calmTypography.meta} className="mc-progressive-loading">
              Loading operational intelligence…
            </p>
          ) : (
            narrative.structuredFindings.map((finding) => (
              <IntelligenceFindingCard key={finding.id} finding={finding} />
            ))
          )}
        </div>

        {companionCommentary.length > 0 && !loading ? (
          <details style={{ marginTop: 28, maxWidth: 780 }}>
            <summary style={{ ...calmTypography.sectionLabel, cursor: "pointer", listStyle: "none" }}>
              Companion commentary (optional)
            </summary>
            <div style={{ marginTop: 14 }}>
              {companionCommentary.map((line) => (
                <p key={line} style={{ ...calmTypography.meta, marginTop: 8, fontStyle: "italic", opacity: 0.88 }}>
                  {line}
                </p>
              ))}
            </div>
          </details>
        ) : null}

        {error ? <p style={{ color: mcColors.red, fontSize: 13, marginTop: 16 }}>{error}</p> : null}

        <div style={{ marginTop: 32, maxWidth: 780 }}>
          {!loading ? (
            <>
              <p style={{ ...calmTypography.sectionLabel, marginBottom: 10 }}>Interpretation</p>
              <p className="mc-signal-continuity" style={calmTypography.body}>{depth === 0 ? narrative.secondaryStory : visibleContent}</p>
              {invisible.batchRecommendations || flowProtection.interruptionPrevented
                ? narrative.compressedAlerts.length > 0 ? (
                    <p style={{ ...calmTypography.meta, marginTop: 18 }}>{narrative.compressedAlerts[0]}</p>
                  ) : null
                : narrative.compressedAlerts.length > 0 ? (
                    <>
                      <p style={{ ...calmTypography.sectionLabel, marginTop: 20, marginBottom: 8 }}>Consolidated signals</p>
                      {narrative.compressedAlerts.map((alert) => (
                        <p key={alert} style={{ ...calmTypography.meta, marginTop: 10, opacity: 0.82 }}>
                          {alert}
                        </p>
                      ))}
                    </>
                  ) : null}
            </>
          ) : null}
        </div>

        {showExpand && nextDepthLabel ? (
          <button
            type="button"
            className="mc-depth-expand mc-luxury-link"
            onClick={() => setDepth((d) => Math.min(3, d + 1) as ProgressiveDepth)}
            style={{
              marginTop: 36,
              padding: 0,
              border: "none",
              background: "none",
              color: mcColors.cyan,
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            {nextDepthLabel} →
          </button>
        ) : null}
      </section>

      {!quiet.suppressQuickLinks && !invisible.suppressLowValueSurfaces && !flow.suppressSecondaryDomains && !opsSanctuary.sanctuaryImmersion ? (
        <section
          style={spatialLayerStyle.secondary}
          className={`mc-fade-in mc-context-emerge mc-supporting-layer ${flow.reduceEnvironmentalVariation || invisible.adaptiveSimplification ? "mc-compressed-layer" : ""}`}
        >
          <p style={calmTypography.sectionLabel}>Supporting context</p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: 18,
              marginTop: 22,
            }}
          >
            {surfaces.map((item) => (
              <button
                key={item.id}
                type="button"
                className="mc-quick-link mc-premium-card mc-luxury-card mc-companion-card"
                onClick={() => onNavigate(item.id)}
                style={{
                  textAlign: "left",
                  padding: "20px 22px",
                  borderRadius: 16,
                  border: "1px solid rgba(255,255,255,0.04)",
                  background: "rgba(255,255,255,0.018)",
                  cursor: "pointer",
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, color: mcColors.text }}>{item.label}</div>
                <div style={{ fontSize: 11, marginTop: 10, color: mcColors.textDim, lineHeight: 1.55 }}>
                  {item.hint}
                </div>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {showHealth && catalog && !invisible.delaySecondaryUpdates && !flowContinuity.interruptionShielding && !opsSanctuary.sanctuaryImmersion ? (
        <details style={spatialLayerStyle.tertiary} className="mc-tertiary-details mc-context-emerge mc-compressed-layer mc-whisper-telemetry">
          <summary
            style={{
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 500,
              color: mcColors.textDim,
              listStyle: "none",
            }}
          >
            Connection health
          </summary>
          <div style={{ marginTop: 18 }}>
            <ConnectionsHealthOverview catalog={catalog} />
          </div>
        </details>
      ) : null}
    </div>
  );
}
