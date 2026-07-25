import { describe, expect, it } from "vitest";

import {
  operationalDeploymentApprovalUiState,
  type ApprovalInboxItem,
} from "@/lib/missionControl/missionControlApprovalInboxApi";

function deploymentInboxItem(overrides: Partial<ApprovalInboxItem> = {}): ApprovalInboxItem {
  return {
    inbox_id: "job-deploy-test",
    lane: "operational_deployment",
    gate_id: "railway_greenfield_deployment_preflight",
    title: "Railway greenfield deployment",
    severity: "critical",
    required_phrases: ["approve job-deploy-test"],
    unlocks: ["governed Railway/Vercel deployment execution"],
    remains_forbidden: ["ungoverned_provider_mutation"],
    risk_tier: "high",
    blast_radius: { preflight_id: "rgf-test" },
    approval_surface: "mission_control_approvals",
    ui_approval_eligible: false,
    approval_execution_enabled: true,
    execution_mode: "operational_deployment_approve",
    mutation_performed: false,
    deployment_inbox_execution_enabled: true,
    deployment_execution_enabled: true,
    ...overrides,
  };
}

describe("deployment_approval_has_button", () => {
  it("renders approve button state for operational deployment items", () => {
    const state = operationalDeploymentApprovalUiState(deploymentInboxItem());
    expect(state.showsApproveButton).toBe(true);
    expect(state.approveDisabled).toBe(false);
  });

  it("disables approve when greenfield execution is planning-only", () => {
    const state = operationalDeploymentApprovalUiState(
      deploymentInboxItem({
        deployment_execution_enabled: false,
        deployment_execution_hint: "Enable Railway greenfield execution to deploy.",
      }),
    );
    expect(state.showsApproveButton).toBe(true);
    expect(state.approveDisabled).toBe(true);
    expect(state.disabledHint).toMatch(/Enable Railway greenfield execution/i);
  });

  it("shows approve button when lane is operational_deployment even without execution_mode", () => {
    const state = operationalDeploymentApprovalUiState(
      deploymentInboxItem({
        execution_mode: "view_only_chat_required",
        deployment_inbox_execution_enabled: undefined,
      }),
    );
    expect(state.showsApproveButton).toBe(true);
  });
});
