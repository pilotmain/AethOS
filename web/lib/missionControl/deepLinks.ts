/** Deep links into Mission Control panels via mc_view query param. */

import type { MissionControlView } from "@/lib/missionControl/views";

const VIEW_PARAM = "mc_view";
export const REPLAY_PARAM = "mc_replay";

export function buildMissionControlUrl(view: MissionControlView, params?: Record<string, string>): string {
  const qs = new URLSearchParams({ [VIEW_PARAM]: view });
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value) qs.set(key, value);
    }
  }
  return `/mission-control?${qs.toString()}`;
}

/** Open Mission Control Research panel scrolled to a saved replay. */
export function buildResearchReplayUrl(replayId: string): string {
  const id = (replayId || "").trim();
  if (!id) return buildMissionControlUrl("deep-research");
  return buildMissionControlUrl("deep-research", { [REPLAY_PARAM]: id });
}

export function readMissionControlReplayId(): string | null {
  if (typeof window === "undefined") return null;
  const id = new URLSearchParams(window.location.search).get(REPLAY_PARAM);
  return id?.trim() ? id.trim() : null;
}

export const MC_DEEP_LINKS = {
  home: "overview",
  agents: "agent-orchestration",
  research: "deep-research",
  approvals: "approval-inbox",
  jobs: "tracked-work",
  providers: "provider-inventory",
  channels: "integrations",
  subagents: "subagent-sessions",
  browser: "browser-evidence",
  gallery: "evidence-gallery",
  library: "research-library",
  blindEval: "blind-model-eval",
  arbiter: "arbiter-panel",
  policy: "channel-tool-policy",
  cron: "cron-governed-jobs",
  automation: "proactive-automation",
  sandbox: "governed-sandbox",
  mcp: "mcp-bridge",
} as const satisfies Record<string, MissionControlView>;

export type McDeepLinkKey = keyof typeof MC_DEEP_LINKS;

export function missionControlHref(key: McDeepLinkKey): string {
  return buildMissionControlUrl(MC_DEEP_LINKS[key]);
}
