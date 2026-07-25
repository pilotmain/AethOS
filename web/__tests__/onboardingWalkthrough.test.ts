import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  TOUR_ANCHORS,
  WALKTHROUGH_VERSION,
  buildWalkthroughSteps,
  hasSeenWalkthrough,
  markWalkthroughSeen,
  resetWalkthrough,
} from "@/lib/onboarding/walkthrough";

/** Minimal localStorage + window shim so the per-user persistence runs in node env. */
function installStorageShim() {
  const store = new Map<string, string>();
  (globalThis as Record<string, unknown>).window = {
    localStorage: {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    },
  };
}

describe("onboarding walkthrough", () => {
  beforeEach(installStorageShim);
  afterEach(() => {
    delete (globalThis as Record<string, unknown>).window;
  });

  it("is value-first, bounded, and opens with a centered welcome", () => {
    const steps = buildWalkthroughSteps();
    expect(steps.length).toBeGreaterThanOrEqual(5);
    expect(steps.length).toBeLessThanOrEqual(15); // comprehensive but still skimmable/skippable
    expect(steps[0].placement).toBe("center"); // welcome (Orient)
    expect(new Set(steps.map((s) => s.id)).size).toBe(steps.length); // unique ids
  });

  it("treats Agents (orchestration) and Multi-Agent Live (interactive) as distinct surfaces", () => {
    const steps = buildWalkthroughSteps();
    const agents = steps.find((s) => s.anchor === TOUR_ANCHORS.navAgents);
    const live = steps.find((s) => s.anchor === TOUR_ANCHORS.navMultiAgent);
    expect(agents).toBeDefined();
    expect(live).toBeDefined();
    expect(agents!.id).not.toBe(live!.id); // two separate steps, two separate panels
    expect(live!.body.toLowerCase()).toContain("real time"); // the live one is the interactive launch pad
  });

  it("greets the signed-in user by name when known", () => {
    expect(buildWalkthroughSteps("Jeremy")[0].title).toContain("Jeremy");
    expect(buildWalkthroughSteps()[0].title.toLowerCase()).toContain("welcome");
  });

  it("every anchored step references a real TOUR_ANCHORS hook (no copy/DOM drift)", () => {
    const known = new Set<string>(Object.values(TOUR_ANCHORS));
    for (const step of buildWalkthroughSteps()) {
      if (step.anchor) expect(known.has(step.anchor)).toBe(true);
    }
  });

  it("the tour points at the key surfaces its copy promises", () => {
    const anchors = buildWalkthroughSteps()
      .map((s) => s.anchor)
      .filter(Boolean);
    for (const expected of [
      TOUR_ANCHORS.modeSelector,
      TOUR_ANCHORS.navSearch,
      TOUR_ANCHORS.navChat,
      TOUR_ANCHORS.navAgents,
      TOUR_ANCHORS.navMultiAgent,
      TOUR_ANCHORS.navArbiter,
      TOUR_ANCHORS.navCompare,
      TOUR_ANCHORS.navResearch,
      TOUR_ANCHORS.navProviders,
      TOUR_ANCHORS.navApprovals,
      TOUR_ANCHORS.navAudit,
    ]) {
      expect(anchors).toContain(expected);
    }
  });

  it("truth-alignment: every anchor a step uses is actually rendered as data-tour in the UI", () => {
    const sources = [
      "components/missionControl/MissionControlSidebar.tsx",
      "components/missionControl/MissionControlHeader.tsx",
      "components/onboarding/OnboardingTour.tsx",
    ]
      .map((p) => readFileSync(resolve(process.cwd(), p), "utf8"))
      .join("\n");
    const usedAnchors = new Set(
      buildWalkthroughSteps()
        .map((s) => s.anchor)
        .filter((a): a is NonNullable<typeof a> => Boolean(a)),
    );
    for (const anchor of usedAnchors) {
      // Rendered either as a literal data-tour="anchor" or via the TOUR_ANCHORS constant.
      const literal = `data-tour="${anchor}"`;
      const constName = Object.entries(TOUR_ANCHORS).find(([, v]) => v === anchor)?.[0];
      const viaConst = constName ? sources.includes(`TOUR_ANCHORS.${constName}`) : false;
      expect(sources.includes(literal) || viaConst).toBe(true);
    }
  });

  it("remembers it was seen, per user, and can be reset to replay", () => {
    expect(hasSeenWalkthrough("alice@x.com")).toBe(false);
    markWalkthroughSeen("alice@x.com");
    expect(hasSeenWalkthrough("alice@x.com")).toBe(true);
    // A different user is unaffected (no cross-account leak).
    expect(hasSeenWalkthrough("bob@x.com")).toBe(false);
    resetWalkthrough("alice@x.com");
    expect(hasSeenWalkthrough("alice@x.com")).toBe(false);
  });

  it("exposes a version so a future redesign can re-show the tour once", () => {
    expect(WALKTHROUGH_VERSION).toBeGreaterThanOrEqual(1);
  });
});
