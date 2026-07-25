import { describe, expect, it } from "vitest";

import {
  ADVANCED_SETTINGS_SECTIONS,
  DEEP_ENGINEERING_ONLY_NAV,
  EXECUTIVE_NAV,
  FLAT_NAV_GROUPS,
  filterAdvancedSectionsForMode,
  filterFlatGroupsForMode,
  isNavVisibleInMode,
  modeNavSummary,
  type FlatNavEntry,
} from "@/lib/missionControl/flatNavigation";
import { MISSION_CONTROL_VIEWS } from "@/lib/missionControl/views";

/**
 * Locks the truth that the header mode selector (Executive / Operator /
 * Deep engineering) actually shapes the dashboard. If someone makes a mode
 * cosmetic again, or the dropdown's promise drifts from what the sidebar
 * renders, these break.
 */
describe("Mission Control mode ruleset", () => {
  it("deep-engineering shows every nav destination", () => {
    for (const group of FLAT_NAV_GROUPS) {
      for (const item of group.items) {
        expect(isNavVisibleInMode(item.id, "deep-engineering")).toBe(true);
      }
    }
    for (const section of ADVANCED_SETTINGS_SECTIONS) {
      for (const item of section.items) {
        expect(isNavVisibleInMode(item.id, "deep-engineering")).toBe(true);
      }
    }
  });

  it("operator hides exactly the deep-only forensic tools and nothing else", () => {
    expect(isNavVisibleInMode("integrity-diagnostics", "operator")).toBe(false);
    expect(isNavVisibleInMode("mission-job-replay", "operator")).toBe(false);
    expect(isNavVisibleInMode("truth-capability-matrix", "operator")).toBe(false);
    // Everyday operator tooling stays visible.
    expect(isNavVisibleInMode("overview", "operator")).toBe(true);
    expect(isNavVisibleInMode("agent-orchestration", "operator")).toBe(true);
    expect(isNavVisibleInMode("provider-inventory", "operator")).toBe(true);
    for (const id of DEEP_ENGINEERING_ONLY_NAV) {
      expect(isNavVisibleInMode(id as never, "operator")).toBe(false);
    }
  });

  it("executive surfaces only the curated cockpit set", () => {
    for (const id of EXECUTIVE_NAV) {
      expect(isNavVisibleInMode(id as never, "executive")).toBe(true);
    }
    // Operator/maker tooling is hidden from executives.
    expect(isNavVisibleInMode("agent-orchestration", "executive")).toBe(false);
    expect(isNavVisibleInMode("provider-inventory", "executive")).toBe(false);
    expect(isNavVisibleInMode("integrity-diagnostics", "executive")).toBe(false);
  });

  it("Home (overview) is reachable in every mode so redirect never strands the user", () => {
    expect(isNavVisibleInMode("overview", "executive")).toBe(true);
    expect(isNavVisibleInMode("overview", "operator")).toBe(true);
    expect(isNavVisibleInMode("overview", "deep-engineering")).toBe(true);
  });

  it("each mode reveals a strictly larger surface than the more restrictive one", () => {
    const exec = modeNavSummary("executive", true).count;
    const operator = modeNavSummary("operator", true).count;
    const deep = modeNavSummary("deep-engineering", true).count;
    expect(exec).toBeGreaterThan(0);
    expect(operator).toBeGreaterThan(exec);
    expect(deep).toBeGreaterThan(operator);
  });

  it("executive collapses the advanced settings tray entirely", () => {
    expect(filterAdvancedSectionsForMode("executive", true)).toHaveLength(0);
    // Deep engineering keeps the advanced tray populated.
    expect(filterAdvancedSectionsForMode("deep-engineering", true).length).toBeGreaterThan(0);
  });

  it("filtered groups drop empty groups and never include hidden items", () => {
    const execGroups = filterFlatGroupsForMode("executive");
    for (const group of execGroups) {
      expect(group.items.length).toBeGreaterThan(0);
      for (const item of group.items) {
        expect(isNavVisibleInMode(item.id, "executive")).toBe(true);
      }
    }
  });

  it("owner-only advanced items stay hidden for non-owners even in deep-engineering", () => {
    const ownerSections = filterAdvancedSectionsForMode("deep-engineering", true);
    const nonOwnerSections = filterAdvancedSectionsForMode("deep-engineering", false);
    const ownerIds = ownerSections.flatMap((s) => s.items.map((i) => String(i.id)));
    const nonOwnerIds = nonOwnerSections.flatMap((s) => s.items.map((i) => String(i.id)));
    expect(ownerIds).toContain("platform-owner");
    expect(nonOwnerIds).not.toContain("platform-owner");
  });

  it("each mode hint describes what it shows (dropdown promise is real)", () => {
    expect(modeNavSummary("executive").hint.toLowerCase()).toContain("cockpit");
    expect(modeNavSummary("operator").hint.toLowerCase()).toContain("everyday");
    expect(modeNavSummary("deep-engineering").hint.toLowerCase()).toContain("everything");
  });

  it("Evidence is the one Multi-agent sub-view kept in nav — visible in operator/deep, hidden from executive", () => {
    expect(isNavVisibleInMode("agent-evidence", "operator")).toBe(true);
    expect(isNavVisibleInMode("agent-evidence", "deep-engineering")).toBe(true);
    expect(isNavVisibleInMode("agent-evidence", "executive")).toBe(false);
  });

  it("the Multi-agent section holds exactly Evidence (the other three were dropped as empty/redundant)", () => {
    const multiAgentSection = ADVANCED_SETTINGS_SECTIONS.find((s) => s.title === "Multi-agent");
    expect(multiAgentSection).toBeDefined();
    const ids = multiAgentSection!.items.map((i) => String(i.id));
    expect(ids).toEqual(["agent-evidence"]);
    expect(multiAgentSection!.items[0].label).toBe("Evidence");
  });

  it("the dropped sub-views are no longer nav items but remain valid (reachable via search/deep-link)", () => {
    const allNav: FlatNavEntry[] = [
      ...FLAT_NAV_GROUPS.flatMap((g) => g.items),
      ...ADVANCED_SETTINGS_SECTIONS.flatMap((s) => s.items),
    ];
    const navIds = new Set(allNav.map((i) => String(i.id)));
    for (const dropped of ["engineering-proposals", "delegated-tasks", "subagent-sessions"]) {
      expect(navIds.has(dropped)).toBe(false); // gone from nav
      // still a real Mission Control view so search/deep-link/renderView keep working
      expect(MISSION_CONTROL_VIEWS).toContain(dropped);
    }
  });
});
