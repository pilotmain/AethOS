import { describe, expect, it } from "vitest";

import {
  domainForView,
  EXECUTIVE_VIEWS,
  filterSectionsForMode,
  isViewVisibleInMode,
  NAV_DOMAINS,
  orderDomains,
  sectionsForDomain,
} from "@/lib/missionControl/sidebarNavigation";
import {
  visiblePrimaryNavCount,
  WORKFLOW_SURFACES,
  workflowForView,
} from "@/lib/missionControl/workflowNavigation";
import { SIDEBAR_SECTIONS, viewDataGroup } from "@/lib/missionControl/views";

describe("missionControlWorkflowNavigation", () => {
  it("exposes six workflow surfaces (overview + five hubs)", () => {
    expect(NAV_DOMAINS).toHaveLength(5);
    expect(WORKFLOW_SURFACES.map((surface) => surface.hubView)).toEqual([
      "workflow-workspaces",
      "workflow-operations",
      "workflow-infrastructure",
      "workflow-intelligence",
      "workflow-settings",
    ]);
  });

  it("maps views to workflow surfaces", () => {
    expect(domainForView("overview")).toBe("overview");
    expect(domainForView("workflow-operations")).toBe("operations");
    expect(domainForView("operational-anomalies")).toBe("operations");
    expect(domainForView("local-workspaces")).toBe("workspaces");
    expect(domainForView("human-living")).toBe("workspaces");
    expect(domainForView("credential-center")).toBe("settings");
    expect(domainForView("enterprise-demo")).toBe("settings");
    expect(domainForView("companion-replay-intelligence")).toBe("intelligence");
    expect(domainForView("infra-kubernetes-runtime")).toBe("infrastructure");
  });

  it("filters deep engineering views in operator mode", () => {
    expect(isViewVisibleInMode("integrity-routes", "operator")).toBe(false);
    expect(isViewVisibleInMode("integrity-routes", "deep-engineering")).toBe(true);
    expect(isViewVisibleInMode("overview", "executive")).toBe(true);
    expect(isViewVisibleInMode("diff-explorer", "executive")).toBe(false);
  });

  it("executive mode exposes a minimal view set", () => {
    expect(EXECUTIVE_VIEWS.length).toBeLessThanOrEqual(8);
    expect(EXECUTIVE_VIEWS).toContain("operational-anomalies");
    expect(EXECUTIVE_VIEWS).toContain("overview");
  });

  it("prioritizes workspaces when preflights are active", () => {
    const ordered = orderDomains(NAV_DOMAINS, { hasActivePreflights: true });
    expect(ordered[0]?.id).toBe("workspaces");
  });

  it("prioritizes intelligence when replay integrity is degraded", () => {
    const ordered = orderDomains(NAV_DOMAINS, { replayIntegrityDegraded: true });
    expect(ordered[0]?.id).toBe("intelligence");
  });

  it("keeps legacy panels reachable under advanced diagnostics", () => {
    const operations = NAV_DOMAINS.find((surface) => surface.id === "operations");
    expect(operations).toBeDefined();
    const sections = filterSectionsForMode(sectionsForDomain(operations!), "deep-engineering");
    const ids = sections.flatMap((section) => section.items.map((item) => item.id));
    expect(ids).toContain("reliability-confidence-forecasting");
    expect(ids).toContain("rfi-runtime-fragility");
  });

  it("reduces visible primary navigation dramatically", () => {
    expect(visiblePrimaryNavCount("operator")).toBeLessThanOrEqual(7);
    const legacyItemCount = SIDEBAR_SECTIONS.reduce((count, section) => count + section.items.length, 0);
    expect(legacyItemCount).toBeGreaterThan(80);
  });

  it("maps hub views to their owning workflow", () => {
    expect(workflowForView("workflow-workspaces")).toBe("workspaces");
    expect(workflowForView("workflow-settings")).toBe("settings");
  });
});

describe("missionControlEngineeringViews", () => {
  it("includes Engineering sidebar section", () => {
    const engineering = SIDEBAR_SECTIONS.find((section) => section.title === "Engineering");
    expect(engineering).toBeDefined();
    expect(engineering?.items.map((item) => item.id)).toContain("local-workspaces");
    expect(engineering?.items.map((item) => item.id)).toContain("pr-proposals");
  });

  it("maps engineering views to engineering data group", () => {
    expect(viewDataGroup("local-workspaces")).toBe("engineering");
    expect(viewDataGroup("architecture-maps")).toBe("engineering");
    expect(viewDataGroup("git-activity")).toBe("engineering");
    expect(viewDataGroup("overview")).toBe("overview");
  });
});
