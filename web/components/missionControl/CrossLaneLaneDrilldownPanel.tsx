"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchMissionControlLaneDrilldown,
  type LaneDrilldownSection,
} from "@/lib/missionControl/missionControlCrossLaneApi";
import { ReplayDeepLinkButton } from "@/components/missionControl/ReplayDeepLinkButton";
import { laneDisplayTitle } from "@/lib/missionControl/crossLaneLaneNavigation";
import {
  buildEvidenceLinkRef,
  buildTimelineLinkRef,
  type ReplayDeepLinkTarget,
} from "@/lib/missionControl/missionControlReplayDeepLink";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type Props = {
  lane: string;
  sessionId: string;
  onClose: () => void;
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
};

type LoadState = "idle" | "loading" | "loaded" | "error";

export function CrossLaneLaneDrilldownPanel({ lane, sessionId, onClose, onOpenReplayDeepLink }: Props) {
  const [sections, setSections] = useState<LaneDrilldownSection[]>([]);
  const [detail, setDetail] = useState<string | undefined>();
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoadState("loading");
      setErrorMessage(null);
      const res = await fetchMissionControlLaneDrilldown(lane, sessionId);
      setSections(res.sections ?? []);
      setDetail(res.detail);
      setLoadState("loaded");
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : "Failed to load lane drilldown");
      setSections([]);
      setLoadState("error");
    }
  }, [lane, sessionId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section
      style={{
        ...mcPanelSectionStyle,
        borderColor: mcColors.cyan,
        boxShadow: "0 0 0 1px rgba(34,211,238,0.15)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
        <div>
          <h3 style={{ margin: "0 0 4px", fontSize: 17, fontWeight: 600, color: mcColors.cyan }}>
            {laneDisplayTitle(lane)} — operational drilldown
          </h3>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            Read-only introspection: receipts, approvals, timelines, contracts, blockers, and audit trails. No mutation
            controls.
          </p>
          {detail ? <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.textDim }}>{detail}</p> : null}
        </div>
        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
          <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()} disabled={loadState === "loading"}>
            Refresh
          </button>
          <button type="button" style={{ ...mcButtonSecondaryStyle, padding: "6px 10px" }} onClick={onClose}>
            Close
          </button>
        </div>
      </div>

      {loadState === "loading" ? (
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>Loading lane drilldown for session {sessionId}…</p>
      ) : null}

      {loadState === "error" && errorMessage ? (
        <div style={{ padding: 12, borderRadius: 8, border: `1px solid ${mcColors.red}`, background: "rgba(239,68,68,0.08)" }}>
          <p style={{ margin: "0 0 8px", color: mcColors.red, fontSize: 13 }}>{errorMessage}</p>
          <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
            Retry drilldown
          </button>
        </div>
      ) : null}

      {loadState === "loaded" && sections.length === 0 ? (
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>No drilldown sections available for this lane.</p>
      ) : null}

      {loadState === "loaded" && sections.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {sections.map((section) => (
            <DrilldownSection
              key={section.section_id}
              section={section}
              lane={lane}
              onOpenReplayDeepLink={onOpenReplayDeepLink}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function DrilldownSection({
  section,
  lane,
  onOpenReplayDeepLink,
}: {
  section: LaneDrilldownSection;
  lane: string;
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
}) {
  const hasRows = (section.rows?.length ?? 0) > 0;
  const hasItems = (section.items?.length ?? 0) > 0;
  const empty = !hasRows && !hasItems;

  return (
    <div
      style={{
        padding: 12,
        borderRadius: 10,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.18)",
      }}
    >
      <h4 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>{section.title}</h4>
      {empty ? (
        <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{section.empty_message ?? "No data."}</p>
      ) : (
        <SectionBody section={section} lane={lane} onOpenReplayDeepLink={onOpenReplayDeepLink} />
      )}
    </div>
  );
}

function SectionBody({
  section,
  lane,
  onOpenReplayDeepLink,
}: {
  section: LaneDrilldownSection;
  lane: string;
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
}) {
  const kind = section.kind;

  if (kind === "key_value" || kind === "rollback_posture" || kind === "verification_evidence") {
    return (
      <div style={{ display: "grid", gap: 6 }}>
        {(section.rows ?? []).map((row) => (
          <Row key={row.label} label={row.label} value={row.value} />
        ))}
        {kind === "verification_evidence" && section.items?.length
          ? section.items.map((item, i) => (
              <pre
                key={i}
                style={{
                  margin: "8px 0 0",
                  padding: 8,
                  fontSize: 11,
                  borderRadius: 8,
                  background: "rgba(255,255,255,0.04)",
                  overflow: "auto",
                  maxHeight: 160,
                }}
              >
                {JSON.stringify(item, null, 2)}
              </pre>
            ))
          : null}
      </div>
    );
  }

  if (kind === "gate_list") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
        {(section.items ?? []).map((gate, i) => (
          <li key={i} style={{ marginBottom: 6, display: "flex", justifyContent: "space-between", gap: 8 }}>
            <span>{String(gate.gate ?? "—")}</span>
            <span style={{ color: gate.passed ? mcColors.green : mcColors.amber }}>
              {gate.passed ? "passed" : "pending"}
            </span>
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "approval_list") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
        {(section.items ?? []).map((item, i) => (
          <li key={i} style={{ marginBottom: 8, padding: 8, borderRadius: 8, background: "rgba(0,0,0,0.2)" }}>
            <div style={{ fontWeight: 500 }}>{String(item.gate ?? "approval")}</div>
            <div style={{ color: mcColors.textMuted, fontSize: 12 }}>
              Status: {String(item.status ?? "—")} · Approved: {String(item.approved ?? false)}
            </div>
            {item.phrase_required ? (
              <div style={{ marginTop: 4, fontSize: 11, color: mcColors.cyan }}>Exact approval phrase required (chat only)</div>
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "timeline" || kind === "audit_trail") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12, maxHeight: 220, overflowY: "auto" }}>
        {(section.items ?? []).map((entry, i) => (
          <li key={i} style={{ marginBottom: 8, borderLeft: `2px solid ${mcColors.border}`, paddingLeft: 10 }}>
            <div style={{ color: mcColors.textDim }}>{String(entry.timestamp ?? entry.recorded_at ?? "—")}</div>
            <div style={{ color: mcColors.text }}>{String(entry.action ?? entry.status ?? entry.source ?? "—")}</div>
            <div style={{ color: mcColors.textMuted }}>{String(entry.detail ?? entry.incident_id ?? entry.summary ?? "")}</div>
            {onOpenReplayDeepLink && entry.action ? (
              <ReplayDeepLinkButton
                onClick={() =>
                  onOpenReplayDeepLink({
                    linkRef: buildTimelineLinkRef({
                      lane,
                      action: String(entry.action ?? ""),
                      timestamp: String(entry.timestamp ?? entry.recorded_at ?? ""),
                    }),
                  })
                }
              />
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "receipt_list") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
        {(section.items ?? []).map((r, i) => (
          <li key={i} style={{ marginBottom: 8, padding: 8, borderRadius: 8, border: `1px solid ${mcColors.border}` }}>
            <div style={{ color: mcColors.cyan }}>{String(r.phase ?? r.status ?? "receipt")}</div>
            <div>{String(r.detail ?? "—")}</div>
            <div style={{ color: mcColors.textDim, marginTop: 4 }}>
              {String(r.recorded_at ?? "—")} · mutation: {String(r.mutation_performed ?? false)}
            </div>
            {onOpenReplayDeepLink ? (
              <ReplayDeepLinkButton
                onClick={() =>
                  onOpenReplayDeepLink({
                    linkRef: buildEvidenceLinkRef(r as Record<string, unknown>),
                  })
                }
              />
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "blocker_list") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
        {(section.items ?? []).map((b, i) => (
          <li key={i} style={{ marginBottom: 6, color: mcColors.amber }}>
            {String(b.gate ?? b.reason ?? "blocker")}: {String(b.detail ?? b.reason ?? "")}
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "execution_contract") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
        {(section.items ?? []).map((item, i) => (
          <li key={i} style={{ marginBottom: 6 }}>
            <span style={{ color: mcColors.textMuted }}>{String(item.label ?? "—")}: </span>
            <span>{String(item.value ?? "")}</span>
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "agent_findings") {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
        {(section.items ?? []).map((f, i) => (
          <li key={i} style={{ marginBottom: 10, padding: 10, borderRadius: 8, background: "rgba(0,0,0,0.25)" }}>
            <div style={{ fontWeight: 600, color: mcColors.cyan }}>{String(f.agent_role_id ?? "agent")}</div>
            <div style={{ marginTop: 4 }}>{String(f.summary ?? f.finding ?? "—")}</div>
            <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>
              Status: {String(f.status ?? "—")} · mutation: {String(f.mutation_performed ?? false)}
            </div>
          </li>
        ))}
      </ul>
    );
  }

  if (kind === "record_list") {
    return (
      <pre
        style={{
          margin: 0,
          padding: 10,
          fontSize: 11,
          borderRadius: 8,
          background: "rgba(255,255,255,0.04)",
          overflow: "auto",
          maxHeight: 240,
        }}
      >
        {JSON.stringify(section.items ?? [], null, 2)}
      </pre>
    );
  }

  return (
    <pre style={{ margin: 0, fontSize: 11, overflow: "auto", maxHeight: 200 }}>
      {JSON.stringify(section.items ?? section.rows ?? [], null, 2)}
    </pre>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 13 }}>
      <span style={{ color: mcColors.textMuted }}>{label}</span>
      <span style={{ color: mcColors.text, textAlign: "right", wordBreak: "break-all" }}>{value}</span>
    </div>
  );
}
