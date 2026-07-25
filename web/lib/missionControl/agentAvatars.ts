// SPDX-License-Identifier: Apache-2.0
// Per-role avatars for the multi-agent visual — a distinct glyph + accent colour per role,
// matched from the agent's label/role. Used by the live communication graph.

export type AgentAvatar = { glyph: string; color: string; initials: string };

type Entry = { keys: string[]; glyph: string; color: string };

// Order matters: first keyword match wins.
const ROLE_TABLE: Entry[] = [
  { keys: ["orchestrat", "director", "lead", "manager"], glyph: "🧠", color: "#22d3ee" },
  { keys: ["architect"], glyph: "🏛️", color: "#60a5fa" },
  { keys: ["develop", "engineer", "coder"], glyph: "💻", color: "#34d399" },
  { keys: ["qa", "test"], glyph: "🧪", color: "#f472b6" },
  { keys: ["devops", "sre", "ops", "operation"], glyph: "🚀", color: "#fb923c" },
  { keys: ["security", "sec"], glyph: "🛡️", color: "#f87171" },
  { keys: ["market"], glyph: "📣", color: "#e879f9" },
  { keys: ["writer", "content", "copy"], glyph: "✍️", color: "#fbbf24" },
  { keys: ["analyst", "analy", "data"], glyph: "📊", color: "#38bdf8" },
  { keys: ["research"], glyph: "🔬", color: "#a78bfa" },
  { keys: ["design"], glyph: "🎨", color: "#f0abfc" },
];

const DEFAULT: Entry = { keys: [], glyph: "🤖", color: "#94a3b8" };

function initialsOf(label: string): string {
  const words = (label || "").trim().split(/[\s_-]+/).filter(Boolean);
  if (words.length === 0) return "··";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

/** Resolve an avatar from an agent's label or role id (e.g. "marketing", "qa_verification"). */
export function agentAvatar(labelOrId: string): AgentAvatar {
  const hay = (labelOrId || "").toLowerCase();
  const match = ROLE_TABLE.find((e) => e.keys.some((k) => hay.includes(k))) || DEFAULT;
  return { glyph: match.glyph, color: match.color, initials: initialsOf(labelOrId) };
}

export type AvatarStyle = "emoji" | "initials" | "dot";

export const AVATAR_STYLES: { id: AvatarStyle; label: string }[] = [
  { id: "emoji", label: "Avatars" },
  { id: "initials", label: "Initials" },
  { id: "dot", label: "Minimal" },
];
