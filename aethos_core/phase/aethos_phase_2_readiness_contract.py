# SPDX-License-Identifier: Apache-2.0
"""
FIX 124 — AethOS Phase 2 readiness contract (machine-readable freeze).

Defines what Phase 1 now means, what Phase 2 may start, allowed/forbidden
capabilities, and agent-execution mapping boundaries. No new Railway production power.
"""

from __future__ import annotations

from typing import Final

PHASE_2_READINESS_FIX: Final[str] = "FIX 124"
PHASE_2_READINESS_SCHEMA_VERSION: Final[str] = "aethos_phase_2_readiness_v1"

# --- Frozen stacks (do not extend without explicit phase sign-off) ---

RAILWAY_PHASE_1_FREEZE_FIX: Final[str] = "FIX 116"
RAILWAY_PHASE_1_FIX_RANGE: Final[str] = "FIX 108–FIX 115"

PRODUCTION_GOVERNANCE_FREEZE_FIX: Final[str] = "FIX 124"
PRODUCTION_GOVERNANCE_FIX_RANGE: Final[str] = "FIX 117–FIX 123"

SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX: Final[str] = "FIX 126"
SOFTWARE_DELIVERY_FIX_RANGE: Final[str] = "FIX 125A–FIX 125I"
SOFTWARE_DELIVERY_PHASE_2_FROZEN: Final[bool] = True

# FIX 126 software delivery cert baselines (global certify must stay at or above).
from aethos_core.software_delivery.software_delivery_phase_2_contract import (  # noqa: E402
    SOFTWARE_DELIVERY_MIN_CERT_MODULES,
    SOFTWARE_DELIVERY_MIN_TEST_COUNT,
)

PRODUCTION_GOVERNANCE_MODULES: Final[tuple[str, ...]] = (
    "production_policy",
    "production_shadow",
    "production_verification",
    "production_rollback_escalation",
    "production_rollout_orchestration",
    "production_canary_shadow_policy",
    "production_incident_command",
)

# --- Product phase definitions ---

PHASE_1_PRODUCT_MEANING: Final[str] = (
    "Governed infrastructure orchestration substrate: staging Railway lifecycle (certified), "
    "production governance stack (policy-complete, no live prod mutations), "
    "channel routing, job truth, memory contract, and certification gate."
)

PHASE_2_PRODUCT_MEANING: Final[str] = (
    "Governed autonomous software delivery and agent execution: issue-to-PR workflows, "
    "workspace intelligence, durable agent jobs, and human-approved code change — "
    "without breaking infra orchestration boundaries or unlocking live production infra."
)

# --- Phase 2 allowed (next capabilities) ---

PHASE_2_ALLOWED_CAPABILITIES: Final[tuple[str, ...]] = (
    "github_issue_to_pr_workflow",
    "bounded_multi_agent_roles",
    "workspace_and_research_lanes",
    "durable_agent_jobs_trigger_dev",
    "mission_control_observability_expansion",
    "software_delivery_preflight_and_verification",
    "human_approved_branch_and_pr_mutations",
    "agent_execution_with_lane_guard",
    "operational_memory_and_job_truth_continuity",
)

# --- Remain forbidden (Phase 2 does not lift these) ---

PHASE_2_FORBIDDEN_CAPABILITIES: Final[tuple[str, ...]] = (
    "live_production_railway_forward",
    "live_production_railway_rollback",
    "autonomous_production_rollout_promotion",
    "autonomous_production_rollback",
    "automatic_incident_closure",
    "auto_merge_to_main",
    "software_delivery_autonomous_merge",
    "software_delivery_autonomous_deploy",
    "software_delivery_railway_mutation",
    "skip_software_delivery_governance_gates",
    "direct_prompt_to_infra_mutation",
    "production_traffic_mutation",
    "production_self_healing_loops",
    "new_railway_production_power_without_phase_signoff",
    "executor_agent_autonomous_mutation",
    "credential_or_secret_exposure_in_customer_comms",
)

# --- Agent execution mapping (tool-loop / Hermes / Pi-inspired → AethOS) ---

AGENT_PATTERN_TOOL_LOOP: Final[str] = "tool_loop"
AGENT_PATTERN_HERMES: Final[str] = "hermes"
AGENT_PATTERN_PI: Final[str] = "pi"

AGENT_EXECUTION_MAPPING: Final[dict[str, str]] = {
    AGENT_PATTERN_TOOL_LOOP: (
        "Tool-using agent loops under governed lanes: chat resolve → route_id ownership "
        "→ preflight/approval → job truth → evidence receipts (no direct infra bypass)."
    ),
    AGENT_PATTERN_HERMES: (
        "Message routing and channel convergence: unified inbound/outbound → orchestration brain "
        "→ lifecycle hydration → policy gates before any adapter mutation."
    ),
    AGENT_PATTERN_PI: (
        "Minimal governed session agent: deterministic routing first, LLM augmentation second, "
        "session-scoped memory and operational thread continuity without autonomous deploy."
    ),
}

# --- Phase 2 entry criteria (certification-enforced) ---

PHASE_2_ENTRY_CRITERIA: Final[tuple[str, ...]] = (
    "make_certify_pass",
    "railway_phase_1_frozen",
    "production_governance_frozen",
    "software_delivery_loop_frozen",
    "mission_control_operator_console_frozen",
    "phase_2_readiness_contract_present",
    "no_live_production_mutation_boundary",
)

# Certification suite size at FIX 124 freeze (modules may grow only with contract update).
CERTIFY_TEST_MODULE_COUNT_FIX_124: Final[int] = 76

CERTIFY_EXPECTED_MIN_TESTS_FIX_124: Final[int] = 120

SOFTWARE_DELIVERY_FIX_125A_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125B_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125C_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125D_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125E_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125F_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125G_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125H_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_125I_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_126_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_127_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_128_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_129_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_130_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_131_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_132_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_133_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_134_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_135_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_136_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_137_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_137B_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_138_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_139_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_140_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_141_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_142_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_143_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_144_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_145_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_146_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_147_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_148_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_149_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_150_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_151_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_152_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_153_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_154_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_155_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_156_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_157_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_158_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_159_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_160_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_161_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_162_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_163_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_164_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_165_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_166_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_167_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_168_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_169_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_170_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_171_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_172_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_173_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_174_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_175_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_176_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_177_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_178_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_179_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_180_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_181_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_182_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_183_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_184_SHIPPED: Final[bool] = True
SOFTWARE_DELIVERY_FIX_185_SHIPPED: Final[bool] = True
MISSION_CONTROL_FIX_186_SHIPPED: Final[bool] = True

# Architectural principle — governance friction & human approval (additive only; FIX 170+ guidance).
GOVERNANCE_FRICTION_APPROVAL_PRINCIPLE_SHIPPED: Final[bool] = True
MISSION_CONTROL_UI_FREEZE_FIX: Final[str] = "FIX 135"
MISSION_CONTROL_OPERATOR_CONSOLE_FROZEN: Final[bool] = True

# Infra orchestration invariant (Phase 2 software delivery must respect).
INFRA_ORCHESTRATION_INVARIANT: Final[str] = (
    "Software delivery agents operate on code/branches/PRs/workspace artifacts. "
    "Infrastructure orchestration (Railway/Vercel/runtime deploy) remains a separate governed lane "
    "with explicit approval phrases and environment policy — agents must not conflate them."
)

AUTONOMOUS_SOFTWARE_DELIVERY_BOUNDARY: Final[str] = (
    "Autonomous delivery completes through governed issue intake → plan → branch → patch → "
    "workspace apply → verify → PR draft → branch push → PR open → human review. "
    "It does not include autonomous merge, production deploy, or promotion."
)
