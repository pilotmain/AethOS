import { describe, expect, it } from "vitest";

import {
  containsHiddenNavigationLeakage,
  resolveVisibleNavigationPath,
  visibleNavigationRegistry,
} from "@/lib/missionControl/visibleNavigationRegistry";

describe("visibleNavigationRegistry", () => {
  it("maps internal Operation Preflights to Approvals for operators", () => {
    expect(resolveVisibleNavigationPath("Operation Preflights", "operator")).toBe(
      "Mission Control → Approvals",
    );
  });

  it("keeps internal labels for deep-engineering mode", () => {
    expect(resolveVisibleNavigationPath("Operation Preflights", "deep-engineering")).toContain(
      "Operation Preflights",
    );
  });

  it("detects hidden navigation leakage in operator copy", () => {
    expect(
      containsHiddenNavigationLeakage("Open Mission Control → Operations → Operation Preflights"),
    ).toBe(true);
    expect(
      containsHiddenNavigationLeakage("Approve in Mission Control → Approvals"),
    ).toBe(false);
  });

  it("lists operator-visible operations without internal panels", () => {
    const reg = visibleNavigationRegistry("operator");
    expect(reg.operatorVisible).toContain("Runtime actions");
    expect(reg.hiddenInternalPanels).toContain("Operation Preflights");
  });
});
