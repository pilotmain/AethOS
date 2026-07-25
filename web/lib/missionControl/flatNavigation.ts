/** Flat Mission Control navigation — one clean sidebar, advanced settings for diagnostics. */

import {
  MISSION_CONTROL_VIEWS,
  VIEW_LABELS,
  type MissionControlView,
} from "@/lib/missionControl/views";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

export type FlatNavExternalId = "chat" | "workspace" | "skills" | "canvas" | "theme";

export type FlatNavEntry = {
  id: MissionControlView | FlatNavExternalId;
  label: string;
  description: string;
  icon: string;
  href?: string;
  /** Hidden unless session.is_platform_owner (env-computed owner). */
  ownerOnly?: boolean;
};

export type FlatNavGroup = {
  id: string;
  label: string;
  items: FlatNavEntry[];
};

/** Primary destinations — everyday operator workflows (§2). */
export const FLAT_NAV_GROUPS: FlatNavGroup[] = [
  {
    id: "work",
    label: "Work",
    items: [
      { id: "overview", label: "Home", description: "Status and quick actions", icon: "⌂" },
      { id: "chat", label: "Chat", description: "Conversations and tasks", icon: "◎", href: "/" },
      { id: "agent-orchestration", label: "Agents", description: "Orchestration and session threads", icon: "⬡" },
      { id: "agent-comms", label: "Multi-Agent Live", description: "Watch a team collaborate in real time", icon: "❖" },
      { id: "approval-inbox", label: "Approvals", description: "Review before anything executes", icon: "✓" },
      { id: "tracked-work", label: "Jobs", description: "Running and recent work", icon: "↻" },
    ],
  },
  {
    id: "build",
    label: "Build",
    items: [
      { id: "deep-research", label: "Research", description: "Compare topics and saved wikis", icon: "⌕" },
      { id: "blind-model-eval", label: "Compare", description: "Blind multi-model comparison", icon: "⇄" },
      { id: "arbiter-panel", label: "Arbiter", description: "Multi-model critique and consensus", icon: "◈" },
      { id: "evidence-gallery", label: "Gallery", description: "Browser evidence and captures", icon: "▣" },
      { id: "research-library", label: "Library", description: "Saved research reports", icon: "▤" },
      { id: "canvas", label: "Canvas", description: "Visual workspace surface", icon: "▦", href: "/canvas" },
      { id: "workspace", label: "Notes", description: "Documents and workspace suite", icon: "☰", href: "/workspace/documents" },
    ],
  },
  {
    id: "connect",
    label: "Connect",
    items: [
      { id: "provider-inventory", label: "Providers", description: "GitHub, Vercel, Railway, and more", icon: "⬢" },
      { id: "integrations", label: "Channels", description: "Telegram, Slack, and messaging", icon: "⇋" },
      { id: "mcp-bridge", label: "MCP", description: "Model Context Protocol tools", icon: "⬚" },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      { id: "settings", label: "Settings", description: "Features and runtime configuration", icon: "⚙" },
      { id: "theme", label: "Theme", description: "Dark, light, or system appearance", icon: "◐" },
    ],
  },
];

/** Power-user configuration and diagnostics (§3) — not everyday navigation. */
export const ADVANCED_SETTINGS_SECTIONS: { title: string; items: FlatNavEntry[] }[] = [
  {
    title: "Multi-agent",
    items: [
      // Evidence is the one sub-view with genuinely distinct, populated content:
      // the granular artifacts (root cause, provider diagnostics, browser, etc.)
      // behind the report shown in the Agents panel. The other former sub-views
      // (Proposals — never produced; Delegated tasks — duplicate of "Recent
      // goals"; Session archive — superseded by the Orchestration board) were
      // dropped from nav. They remain reachable via search / deep-link.
      { id: "agent-evidence", label: "Evidence", description: "Deep evidence artifacts — root cause, provider, browser", icon: "◎" },
    ],
  },
  {
    title: "Configuration",
    items: [
      { id: "research-config", label: "Research & search", description: "Web search provider keys", icon: "⌕" },
      { id: "runtime-tunnel", label: "Runtime tunnel", description: "Ngrok and webhook tunneling", icon: "⇱" },
      { id: "channel-tool-policy", label: "Channel tools", description: "Per-channel tool policy", icon: "⇋" },
      { id: "cron-governed-jobs", label: "Cron jobs", description: "Scheduled governed jobs", icon: "↻" },
      { id: "proactive-automation", label: "Automation", description: "Proactive automation rules", icon: "⚡" },
      { id: "governed-sandbox", label: "Sandbox", description: "Governed sandbox sessions", icon: "▢" },
      { id: "credential-center", label: "Credentials", description: "Vault and credential center", icon: "⬢" },
    ],
  },
  {
    title: "Diagnostics",
    items: [
      { id: "observability", label: "Observability", description: "Runtime and connection health", icon: "◉" },
      { id: "system-health", label: "System health", description: "Platform health snapshot", icon: "♥" },
      { id: "audit-logs", label: "Audit logs", description: "Governance audit trail", icon: "☰" },
      { id: "integrity-diagnostics", label: "Integrity", description: "Route and feature integrity", icon: "⚠" },
      { id: "truth-capability-matrix", label: "Capability matrix", description: "Live capability evidence", icon: "▣" },
      { id: "truth-provider-readiness", label: "Provider readiness", description: "Adapter readiness truth", icon: "⬢" },
      { id: "enterprise-doctor", label: "System doctor", description: "Enterprise health checks", icon: "⚕" },
    ],
  },
  {
    title: "Operations",
    items: [
      { id: "mission-job-replay", label: "Job replay", description: "Replay governed job runs", icon: "↺" },
      { id: "mutation-audit", label: "Mutation audit", description: "Governed mutation history", icon: "✓" },
      {
        id: "platform-owner",
        label: "Owner",
        description: "Grant, extend, and revoke beta access",
        icon: "◆",
        ownerOnly: true,
      },
      {
        id: "users-roles",
        label: "Users & roles",
        description: "Set per-user roles (read-only, operator, approver)",
        icon: "◍",
        ownerOnly: true,
      },
      { id: "operational-intelligence", label: "Operational intel", description: "Cross-surface intelligence", icon: "◈" },
      { id: "cross-lane-operations", label: "Cross-lane ops", description: "Multi-lane control surface", icon: "⇄" },
      { id: "activity-feed", label: "Activity feed", description: "Channel and system activity", icon: "◎" },
    ],
  },
  {
    title: "Pilot & launch",
    items: [
      { id: "pilot-validation-trust-board", label: "Pilot validation", description: "Pilot trust board", icon: "✓" },
      { id: "dogfood-pilot-chain", label: "Dogfood chain", description: "Internal pilot chain", icon: "↻" },
      { id: "launch-operations-center", label: "Launch ops", description: "Launch operations center", icon: "⌂" },
      { id: "saas-launch-readiness", label: "Launch readiness", description: "SaaS launch assessment", icon: "▣" },
      { id: "tenant-onboarding", label: "Tenant onboarding", description: "Onboarding activation", icon: "⬡" },
    ],
  },
  {
    title: "Workflow hubs",
    items: [
      { id: "workflow-workspaces", label: "Workspaces hub", description: "Workspace workflow hub", icon: "☰" },
      { id: "workflow-operations", label: "Operations hub", description: "Operations workflow hub", icon: "↻" },
      { id: "workflow-infrastructure", label: "Infrastructure hub", description: "Infrastructure workflow hub", icon: "⬢" },
      { id: "workflow-intelligence", label: "Intelligence hub", description: "Intelligence workflow hub", icon: "◈" },
      { id: "workflow-settings", label: "Settings hub", description: "Settings workflow hub", icon: "⚙" },
    ],
  },
];

/** Views folded into a primary nav destination (still reachable via search / deep link). */
export const MERGED_INTO_PRIMARY: Record<string, MissionControlView> = {
  "active-agents": "agent-orchestration",
  "agent-timelines": "agent-orchestration",
  "coordination-graph": "agent-orchestration",
  "operation-preflights": "approval-inbox",
  "runtime-actions": "approval-inbox",
  "engineering-execution": "approval-inbox",
  "cross-lane-operations": "approval-inbox",
  "web-intelligence": "deep-research",
  "research-intelligence": "deep-research",
  "provider-connections": "provider-inventory",
};

const primaryMcIds = new Set<MissionControlView>();
for (const group of FLAT_NAV_GROUPS) {
  for (const item of group.items) {
    if (!item.href && item.id !== "theme") {
      primaryMcIds.add(item.id as MissionControlView);
    }
  }
}

const advancedMcIds = new Set<MissionControlView>();
for (const section of ADVANCED_SETTINGS_SECTIONS) {
  for (const item of section.items) {
    advancedMcIds.add(item.id as MissionControlView);
  }
}

export const MAIN_NAV_VIEW_IDS = primaryMcIds;
export const ADVANCED_SETTINGS_VIEW_IDS = advancedMcIds;

export function isMainNavView(view: MissionControlView): boolean {
  return MAIN_NAV_VIEW_IDS.has(view);
}

export function isAdvancedSettingsView(view: MissionControlView): boolean {
  return ADVANCED_SETTINGS_VIEW_IDS.has(view);
}

export function isFlatNavReachableView(view: MissionControlView): boolean {
  return isMainNavView(view) || isAdvancedSettingsView(view);
}

export function flatNavLabel(view: MissionControlView): string {
  for (const group of FLAT_NAV_GROUPS) {
    const hit = group.items.find((item) => item.id === view);
    if (hit) return hit.label;
  }
  for (const section of ADVANCED_SETTINGS_SECTIONS) {
    const hit = section.items.find((item) => item.id === view);
    if (hit) return hit.label;
  }
  return VIEW_LABELS[view] ?? view;
}

export function flatNavDescription(view: MissionControlView): string {
  for (const group of FLAT_NAV_GROUPS) {
    const hit = group.items.find((item) => item.id === view);
    if (hit) return hit.description;
  }
  for (const section of ADVANCED_SETTINGS_SECTIONS) {
    const hit = section.items.find((item) => item.id === view);
    if (hit) return hit.description;
  }
  return "";
}

export type NavSearchResult = {
  id: MissionControlView | FlatNavExternalId;
  label: string;
  description: string;
  section: string;
  href?: string;
  ownerOnly?: boolean;
};

export function buildNavSearchIndex(): NavSearchResult[] {
  const seen = new Set<string>();
  const out: NavSearchResult[] = [];

  const push = (entry: FlatNavEntry, section: string) => {
    const key = String(entry.id);
    if (seen.has(key)) return;
    seen.add(key);
    out.push({
      id: entry.id,
      label: entry.label,
      description: entry.description,
      section,
      href: entry.href,
      ownerOnly: entry.ownerOnly,
    });
  };

  for (const group of FLAT_NAV_GROUPS) {
    for (const item of group.items) {
      push(item, group.label);
    }
  }
  for (const section of ADVANCED_SETTINGS_SECTIONS) {
    for (const item of section.items) {
      push(item, `Advanced · ${section.title}`);
    }
  }

  for (const view of MISSION_CONTROL_VIEWS) {
    if (seen.has(view)) continue;
    seen.add(view);
    out.push({
      id: view,
      label: VIEW_LABELS[view] ?? view,
      description: "Power-user panel — search jump",
      section: "All panels",
    });
  }

  return out;
}

export function filterNavSearch(query: string, isPlatformOwner = false): NavSearchResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return buildNavSearchIndex().filter(
    (item) =>
      (!item.ownerOnly || isPlatformOwner) &&
      (item.label.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q) ||
        String(item.id).toLowerCase().includes(q)),
  );
}

/** @deprecated Use flat nav — kept for deep-link tests. */
export function flatNavRedirectForView(view: MissionControlView): MissionControlView {
  return MERGED_INTO_PRIMARY[view] ?? view;
}

/* ──────────────────────────── Mode ruleset ────────────────────────────
 * The header mode selector (Executive / Operator / Deep engineering) is NOT
 * cosmetic. These sets are the single source of truth for what each mode shows:
 * the sidebar renders exactly what `isNavVisibleInMode` allows, the shell
 * redirects away from a view that the chosen mode hides, and the header summary
 * counts the same set — so what the dropdown promises is what the user gets.
 *
 *   deep-engineering — everything (full surface: diagnostics, integrity, replay)
 *   operator (default) — everyday operations: everything EXCEPT the deep-only tools
 *   executive — a focused high-level cockpit: only the curated EXECUTIVE_NAV set
 */

/** Power/forensic surfaces shown only in deep-engineering mode. */
export const DEEP_ENGINEERING_ONLY_NAV = new Set<string>([
  // Diagnostics & truth tooling
  "integrity-diagnostics",
  "truth-capability-matrix",
  "truth-provider-readiness",
  "enterprise-doctor",
  "observability",
  // Replay & mutation forensics
  "mission-job-replay",
  "mutation-audit",
  "operational-intelligence",
  "cross-lane-operations",
  // Secondary legacy workflow-hub surfaces
  "workflow-workspaces",
  "workflow-operations",
  "workflow-infrastructure",
  "workflow-intelligence",
  "workflow-settings",
]);

/** The only destinations executive mode surfaces — a high-signal cockpit. */
export const EXECUTIVE_NAV = new Set<string>([
  "overview",
  "chat",
  "approval-inbox",
  "tracked-work",
  "settings",
  "theme",
]);

/** True when a nav destination should be visible in the given mode. */
export function isNavVisibleInMode(
  id: MissionControlView | FlatNavExternalId,
  mode: MissionControlMode,
): boolean {
  const key = String(id);
  if (mode === "deep-engineering") return true;
  if (mode === "executive") return EXECUTIVE_NAV.has(key);
  return !DEEP_ENGINEERING_ONLY_NAV.has(key); // operator
}

/** Primary nav groups filtered + emptied-groups dropped, for the given mode. */
export function filterFlatGroupsForMode(mode: MissionControlMode): FlatNavGroup[] {
  return FLAT_NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => isNavVisibleInMode(item.id, mode)),
  })).filter((group) => group.items.length > 0);
}

/** Advanced settings sections filtered by mode + owner, emptied sections dropped. */
export function filterAdvancedSectionsForMode(
  mode: MissionControlMode,
  isPlatformOwner: boolean,
): { title: string; items: FlatNavEntry[] }[] {
  return ADVANCED_SETTINGS_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter(
      (item) => (!item.ownerOnly || isPlatformOwner) && isNavVisibleInMode(item.id, mode),
    ),
  })).filter((section) => section.items.length > 0);
}

export type ModeNavSummary = { label: string; hint: string; count: number };

const MODE_NAV_LABELS: Record<MissionControlMode, string> = {
  executive: "Executive",
  operator: "Operator",
  "deep-engineering": "Deep engineering",
};

const MODE_NAV_HINTS: Record<MissionControlMode, string> = {
  executive: "High-level cockpit — status, approvals & jobs only",
  operator: "Everyday operations — full tooling, deep diagnostics hidden",
  "deep-engineering": "Everything — diagnostics, integrity, replay & truth tooling",
};

/** Human-facing label, one-line hint, and the count of panels a mode reveals. */
export function modeNavSummary(mode: MissionControlMode, isPlatformOwner = false): ModeNavSummary {
  let count = 0;
  for (const group of filterFlatGroupsForMode(mode)) {
    count += group.items.filter((item) => item.id !== "theme").length;
  }
  for (const section of filterAdvancedSectionsForMode(mode, isPlatformOwner)) {
    count += section.items.length;
  }
  return { label: MODE_NAV_LABELS[mode], hint: MODE_NAV_HINTS[mode], count };
}
