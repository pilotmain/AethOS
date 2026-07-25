import { describe, expect, it } from "vitest";

import {
  formatProviderEvidenceItem,
  providerEvidenceSectionTitle,
  providerEvidenceSourceLabel,
} from "@/lib/missionControl/providerEvidence";

describe("providerEvidence", () => {
  it("labels provider-specific evidence sections", () => {
    expect(providerEvidenceSectionTitle("railway", "list_deployments")).toBe("Railway deployment evidence");
    expect(providerEvidenceSectionTitle("github", "workflow_runs")).toBe("GitHub workflow evidence");
    expect(providerEvidenceSectionTitle("vercel", "list_domains")).toBe("Vercel domain evidence");
  });

  it("formats provider-specific evidence items without flattening semantics", () => {
    const railway = formatProviderEvidenceItem("railway", {
      source: "railway_api",
      type: "deployment",
      confidence: "confirmed",
      message: "Deployment dep-1 failed on main",
    });
    expect(railway).toContain("Railway API");
    expect(railway).toContain("Deployment");
    expect(railway).toContain("dep-1 failed");

    const github = formatProviderEvidenceItem("github", {
      source: "github_api",
      type: "workflow_run",
      confidence: "confirmed",
      message: "CI workflow failed on push",
    });
    expect(github).toContain("GitHub API");
    expect(github).toContain("Workflow run");

    const vercel = formatProviderEvidenceItem("vercel", {
      source: "vercel_api",
      type: "domain_record",
      confidence: "confirmed",
      message: "invoicepilot.com verified",
    });
    expect(vercel).toContain("Vercel API");
    expect(vercel).toContain("Domain");
    expect(vercel).toContain("invoicepilot.com");
  });

  it("maps provider api source labels", () => {
    expect(providerEvidenceSourceLabel("railway_api")).toBe("Railway API");
    expect(providerEvidenceSourceLabel("github_api")).toBe("GitHub API");
    expect(providerEvidenceSourceLabel("vercel_api")).toBe("Vercel API");
  });
});
