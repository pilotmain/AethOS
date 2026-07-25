/**
 * First-run walkthrough — a short, skippable, replayable tour of Mission Control.
 *
 * Design principles (kept deliberately honest):
 *  - Truth-aligned: every step that points at the UI uses an anchor from
 *    TOUR_ANCHORS, and the components render `data-tour={TOUR_ANCHORS.x}` on the
 *    real element. Copy and DOM cannot drift — they share the same constant.
 *  - Short: ~6 steps, value-first, never a feature dump.
 *  - Always escapable + replayable (the "?" launcher reopens it any time).
 *  - If an anchor isn't on screen (e.g. hidden by the current mode), the step
 *    degrades to a centered card with copy that is still accurate.
 */

/** Stable hooks the components attach via `data-tour=`. Steps reference the same values. */
export const TOUR_ANCHORS = {
  modeSelector: "mode-selector",
  navSearch: "nav-search",
  navChat: "nav-chat",
  navAgents: "nav-agents",
  navMultiAgent: "nav-multiagent",
  navArbiter: "nav-arbiter",
  navCompare: "nav-compare",
  navResearch: "nav-research",
  navProviders: "nav-providers",
  navApprovals: "nav-approvals",
  navAudit: "nav-audit",
  launcher: "tour-launcher",
} as const;

export type TourAnchor = (typeof TOUR_ANCHORS)[keyof typeof TOUR_ANCHORS];

export type TourPlacement = "center" | "right" | "bottom" | "left";

export type WalkthroughStep = {
  id: string;
  title: string;
  body: string;
  /** Omitted → centered welcome/summary card. */
  anchor?: TourAnchor;
  placement?: TourPlacement;
};

/** Bump when the steps change materially so returning users see the new tour once. */
export const WALKTHROUGH_VERSION = 3;

export function buildWalkthroughSteps(displayName?: string): WalkthroughStep[] {
  const hi = displayName ? `Welcome, ${displayName}` : "Welcome to AethOS";
  return [
    {
      id: "welcome",
      title: `${hi} 👋`,
      body:
        "AethOS is your governed AI operations cockpit. You describe a goal, AethOS plans the work across models and tools — and nothing happens to your systems until you approve it. Here's a 60-second run-down of the layout.",
      placement: "center",
    },
    {
      id: "mode",
      title: "Pick how much you see",
      body:
        "This selector switches your view. Executive is a high-level cockpit (status, approvals, jobs). Operator is the full everyday toolkit. Deep engineering reveals everything — diagnostics, integrity and replay. The caption under it tells you exactly what each shows.",
      anchor: TOUR_ANCHORS.modeSelector,
      placement: "bottom",
    },
    {
      id: "navigate",
      title: "Find anything fast",
      body:
        "The left rail is your map. Type here to jump to any panel by name — Settings, Providers, Approvals, the Capability Matrix and more. The rail also adapts to the mode you picked.",
      anchor: TOUR_ANCHORS.navSearch,
      placement: "right",
    },
    {
      id: "chat",
      title: "Talk to AethOS",
      body:
        "Chat is where you give AethOS a goal in plain language. It breaks the goal into steps, picks the right models and tools, and shows you its plan before acting.",
      anchor: TOUR_ANCHORS.navChat,
      placement: "right",
    },
    {
      id: "agents",
      title: "Agents — your orchestration view",
      body:
        "Agents is where coordinated multi-agent runs are managed and observed: the sessions that have run, who did what, the hand-offs between them, and the artifacts they produced. It's the control room, not the launch pad.",
      anchor: TOUR_ANCHORS.navAgents,
      placement: "right",
    },
    {
      id: "multiagent",
      title: "Multi-Agent Live — watch it happen",
      body:
        "This is the launch pad: drop in a goal and AethOS spins up a whole team — planner, researcher, builder, reviewer — and you watch them talk to each other and hand off work in real time. Try it with any goal; runs you start here also show up back in Agents.",
      anchor: TOUR_ANCHORS.navMultiAgent,
      placement: "right",
    },
    {
      id: "arbiter",
      title: "Don't bet on one model",
      body:
        "Arbiter asks several top models the same question, then critiques and reconciles their answers into one trustworthy result — with the disagreements surfaced, not hidden.",
      anchor: TOUR_ANCHORS.navArbiter,
      placement: "right",
    },
    {
      id: "compare",
      title: "Find your best model, blind",
      body:
        "Compare runs a blind, side-by-side model eval: ask once, see each model's answer without labels, and pick the winner. The fastest way to learn which model fits your work.",
      anchor: TOUR_ANCHORS.navCompare,
      placement: "right",
    },
    {
      id: "research",
      title: "Deep research, cited",
      body:
        "Research digs across the web and your saved sources and writes you a cited report — saved to the Library so you can come back to it.",
      anchor: TOUR_ANCHORS.navResearch,
      placement: "right",
    },
    {
      id: "providers",
      title: "Connect your tools",
      body:
        "Providers is where you link GitHub, Vercel, Railway and more. AethOS only ever acts through the providers you connect — and only with the access you grant.",
      anchor: TOUR_ANCHORS.navProviders,
      placement: "right",
    },
    {
      id: "approvals",
      title: "You're always in control",
      body:
        "AethOS is governed: anything that changes a real system waits for your sign-off in Approvals. You review exactly what will happen — and can approve or reject — before it runs.",
      anchor: TOUR_ANCHORS.navApprovals,
      placement: "right",
    },
    {
      id: "audit",
      title: "Nothing happens off the record",
      body:
        "Every governed action is written to Audit Logs (under Advanced settings) — a full, timestamped trail of what ran, when, and why. You can always see exactly what AethOS did.",
      anchor: TOUR_ANCHORS.navAudit,
      placement: "right",
    },
    {
      id: "truth",
      title: "AethOS tells you the truth",
      body:
        "Flip this to Deep engineering, then open the Capability Matrix (under Advanced settings) to see what AethOS can really do — claimed vs. actually verified, per capability. No marketing, just evidence. You're all set! Reopen this tour anytime from the “?” button, bottom-right.",
      anchor: TOUR_ANCHORS.modeSelector,
      placement: "bottom",
    },
  ];
}

/* ───────────────────────── per-user persistence ───────────────────────── */

const storageKey = (scope: string) => `aethos.walkthrough.v${WALKTHROUGH_VERSION}.${scope || "anon"}`;

type WalkthroughRecord = { seenAt: string };

function readStorage(scope: string): WalkthroughRecord | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey(scope));
    return raw ? (JSON.parse(raw) as WalkthroughRecord) : null;
  } catch {
    return null;
  }
}

/** True once the user has completed or dismissed the tour (won't auto-open again). */
export function hasSeenWalkthrough(scope: string): boolean {
  return readStorage(scope) != null;
}

export function markWalkthroughSeen(scope: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(storageKey(scope), JSON.stringify({ seenAt: new Date().toISOString() }));
  } catch {
    /* private mode / quota — non-fatal, tour just re-offers next load */
  }
}

export function resetWalkthrough(scope: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(storageKey(scope));
  } catch {
    /* non-fatal */
  }
}
