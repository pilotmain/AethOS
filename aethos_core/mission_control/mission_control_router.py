# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — Mission Control cross-lane observability router."""

from __future__ import annotations

from aethos_core.mission_control.cross_lane.cross_lane_contract import MISSION_CONTROL_ROUTE_ID
from aethos_core.mission_control.cross_lane.snapshot_renderer import (
    render_attention_queue,
    render_audit_search,
    render_health_summary,
    render_snapshot,
    render_timeline,
)
from aethos_core.mission_control.cross_lane.snapshot_service import (
    build_mission_control_snapshot,
    is_mission_control_observability_intent,
    search_mission_control_audit,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_CONTROL_ROUTE_ID,
        "matched_module": "mission_control.mission_control_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "mutation_scope": "mission_control_observability_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "observability_not_mutation",
        **extra,
    }


def route_mission_control_observability(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_router import route_governance_doctrine
    from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_router import (
        route_governance_role_architecture,
    )
    from aethos_core.mission_control.governance_collaboration.governance_collaboration_router import (
        route_governance_collaboration,
    )
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_router import (
        route_governance_deliberation,
    )
    from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_router import (
        route_mission_readiness_review,
    )
    from aethos_core.mission_control.mission_orchestration.mission_orchestration_router import (
        route_mission_orchestration,
    )
    from aethos_core.mission_control.mission_strategy.mission_strategy_router import route_mission_strategy
    from aethos_core.mission_control.governance_simulation.governance_simulation_router import (
        route_governance_simulation,
    )
    from aethos_core.mission_control.governance_insights.governance_insights_router import route_governance_insights
    from aethos_core.mission_control.operator_guidance.operator_guidance_router import route_operator_guidance
    from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_router import route_knowledge_spaces
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_router import (
        route_cross_session_operational_memory,
    )
    from aethos_core.mission_control.operational_memory.operational_memory_router import route_operational_memory
    from aethos_core.mission_control.rerun_planning.rerun_plan_router import route_governed_rerun_plan

    raw = (text or "").strip()
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_router import (
        route_pilot_validation_trust_board,
    )
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_router import (
        route_repo_pilot_readiness_dashboard,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_router import (
        route_end_to_end_repo_development_pilot_harness,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_router import (
        route_governed_chat_command_invocation_from_handoff,
    )
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_router import (
        route_frozen_gate_execution_request_adapter,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_router import (
        route_frozen_gate_intake_preview,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_router import (
        route_gate_routed_lane_entry_handoff,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_router import (
        route_human_lane_admission_decision,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_router import (
        route_governed_lane_readiness_board,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_router import (
        route_governed_lane_entry_recommendation,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_router import (
        route_gate_routed_package_outcome_review,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_router import (
        route_governed_task_execution_coordination,
    )
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_router import (
        route_bounded_execution_participation,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_router import (
        route_mission_authorization,
    )
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_router import (
        route_work_package_readiness_lane_admission,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_router import (
        route_bounded_delivery_work_packages,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_router import (
        route_execution_handoff_coordination,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_router import (
        route_human_decision_board,
    )
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_router import (
        route_mission_planning_deliberation,
    )
    from aethos_core.mission_control.mission_planning.mission_planning_router import (
        route_mission_planning,
    )
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_router import (
        route_constitutional_synthesis,
    )
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_router import (
        route_constitutional_pluralism,
    )
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_router import (
        route_constitutional_legitimacy,
    )
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_router import (
        route_constitutional_audit,
    )
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_router import (
        route_constitutional_ethics,
    )
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_router import (
        route_institutional_existential_risk,
    )
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_router import (
        route_institutional_external_relations,
    )
    from aethos_core.mission_control.institutional_identity.institutional_identity_router import (
        route_institutional_identity,
    )
    from aethos_core.mission_control.governance_evolution.governance_evolution_router import route_governance_evolution
    from aethos_core.mission_control.governance_resilience.governance_resilience_router import route_governance_resilience
    from aethos_core.mission_control.governance_coherence.governance_coherence_router import route_governance_coherence
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_router import (
        route_governance_policy_interpretation,
    )

    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_router import (
        route_issue_intent_alignment,
    )

    issue_intent_alignment = route_issue_intent_alignment(raw, session_id=session_id)
    if issue_intent_alignment is not None:
        return issue_intent_alignment
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_router import (
        route_independent_repository_trust_expansion,
    )

    independent_repository_trust_expansion = route_independent_repository_trust_expansion(
        raw, session_id=session_id
    )
    if independent_repository_trust_expansion is not None:
        return independent_repository_trust_expansion
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_router import (
        route_pilotos_ui_pilot_arc_orchestrator,
    )

    pilotos_ui_pilot_arc = route_pilotos_ui_pilot_arc_orchestrator(raw, session_id=session_id)
    if pilotos_ui_pilot_arc is not None:
        return pilotos_ui_pilot_arc

    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_router import (
        route_pilotos_ui_trust_report_freeze,
    )

    pilotos_ui_trust_report_freeze = route_pilotos_ui_trust_report_freeze(raw, session_id=session_id)
    if pilotos_ui_trust_report_freeze is not None:
        return pilotos_ui_trust_report_freeze

    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_router import (
        route_atlas_trader_pilot_arc_orchestrator,
    )

    atlas_trader_pilot_arc = route_atlas_trader_pilot_arc_orchestrator(raw, session_id=session_id)
    if atlas_trader_pilot_arc is not None:
        return atlas_trader_pilot_arc

    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_router import (
        route_atlas_trader_trust_report_freeze,
    )

    atlas_trader_trust_report_freeze = route_atlas_trader_trust_report_freeze(raw, session_id=session_id)
    if atlas_trader_trust_report_freeze is not None:
        return atlas_trader_trust_report_freeze

    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_router import (
        route_nexora_pilot_arc_orchestrator,
    )

    nexora_pilot_arc = route_nexora_pilot_arc_orchestrator(raw, session_id=session_id)
    if nexora_pilot_arc is not None:
        return nexora_pilot_arc

    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_router import (
        route_nexora_trust_report_freeze,
    )

    nexora_trust_report_freeze = route_nexora_trust_report_freeze(raw, session_id=session_id)
    if nexora_trust_report_freeze is not None:
        return nexora_trust_report_freeze

    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_router import (
        route_dogfood_pilot_trust_report_freeze,
    )

    dogfood_pilot_trust_report_freeze = route_dogfood_pilot_trust_report_freeze(raw, session_id=session_id)
    if dogfood_pilot_trust_report_freeze is not None:
        return dogfood_pilot_trust_report_freeze
    pilot_validation_trust_board = route_pilot_validation_trust_board(raw, session_id=session_id)
    if pilot_validation_trust_board is not None:
        return pilot_validation_trust_board
    repo_pilot_readiness_dashboard = route_repo_pilot_readiness_dashboard(raw, session_id=session_id)
    if repo_pilot_readiness_dashboard is not None:
        return repo_pilot_readiness_dashboard
    end_to_end_repo_development_pilot_harness = route_end_to_end_repo_development_pilot_harness(
        raw, session_id=session_id
    )
    if end_to_end_repo_development_pilot_harness is not None:
        return end_to_end_repo_development_pilot_harness
    governed_chat_command_invocation_from_handoff = route_governed_chat_command_invocation_from_handoff(
        raw, session_id=session_id
    )
    if governed_chat_command_invocation_from_handoff is not None:
        return governed_chat_command_invocation_from_handoff
    frozen_gate_execution_request_adapter = route_frozen_gate_execution_request_adapter(
        raw, session_id=session_id
    )
    if frozen_gate_execution_request_adapter is not None:
        return frozen_gate_execution_request_adapter
    frozen_gate_intake_preview = route_frozen_gate_intake_preview(raw, session_id=session_id)
    if frozen_gate_intake_preview is not None:
        return frozen_gate_intake_preview
    gate_routed_lane_entry_handoff = route_gate_routed_lane_entry_handoff(raw, session_id=session_id)
    if gate_routed_lane_entry_handoff is not None:
        return gate_routed_lane_entry_handoff
    human_lane_admission_decision = route_human_lane_admission_decision(raw, session_id=session_id)
    if human_lane_admission_decision is not None:
        return human_lane_admission_decision
    governed_lane_readiness_board = route_governed_lane_readiness_board(raw, session_id=session_id)
    if governed_lane_readiness_board is not None:
        return governed_lane_readiness_board
    governed_lane_entry_recommendation = route_governed_lane_entry_recommendation(raw, session_id=session_id)
    if governed_lane_entry_recommendation is not None:
        return governed_lane_entry_recommendation
    gate_routed_package_outcome_review = route_gate_routed_package_outcome_review(raw, session_id=session_id)
    if gate_routed_package_outcome_review is not None:
        return gate_routed_package_outcome_review
    governed_task_execution_coordination = route_governed_task_execution_coordination(raw, session_id=session_id)
    if governed_task_execution_coordination is not None:
        return governed_task_execution_coordination
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_router import (
        route_bounded_multi_agent_delivery_execution,
    )

    bounded_multi_agent_delivery_execution = route_bounded_multi_agent_delivery_execution(
        raw, session_id=session_id
    )
    if bounded_multi_agent_delivery_execution is not None:
        return bounded_multi_agent_delivery_execution
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_router import (
        route_agent_execution_quality_throughput_metrics,
    )

    agent_execution_quality_throughput_metrics = route_agent_execution_quality_throughput_metrics(
        raw, session_id=session_id
    )
    if agent_execution_quality_throughput_metrics is not None:
        return agent_execution_quality_throughput_metrics
    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_router import (
        route_cross_repository_multi_agent_delivery_validation,
    )

    cross_repository_validation = route_cross_repository_multi_agent_delivery_validation(
        raw, session_id=session_id
    )
    if cross_repository_validation is not None:
        return cross_repository_validation
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_router import (
        route_governed_merge_lifecycle,
    )

    governed_merge_lifecycle = route_governed_merge_lifecycle(raw, session_id=session_id)
    if governed_merge_lifecycle is not None:
        return governed_merge_lifecycle
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_router import (
        route_governed_deploy_lifecycle,
    )

    governed_deploy_lifecycle = route_governed_deploy_lifecycle(raw, session_id=session_id)
    if governed_deploy_lifecycle is not None:
        return governed_deploy_lifecycle
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_router import (
        route_governed_monitoring_lifecycle,
    )

    governed_monitoring_lifecycle = route_governed_monitoring_lifecycle(raw, session_id=session_id)
    if governed_monitoring_lifecycle is not None:
        return governed_monitoring_lifecycle
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_router import (
        route_governed_rollback_lifecycle,
    )

    governed_rollback_lifecycle = route_governed_rollback_lifecycle(raw, session_id=session_id)
    if governed_rollback_lifecycle is not None:
        return governed_rollback_lifecycle
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_router import (
        route_repository_knowledge_graph,
    )

    repository_knowledge_graph = route_repository_knowledge_graph(raw, session_id=session_id)
    if repository_knowledge_graph is not None:
        return repository_knowledge_graph
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_router import (
        route_governed_application_generation,
    )

    governed_application_generation = route_governed_application_generation(raw, session_id=session_id)
    if governed_application_generation is not None:
        return governed_application_generation

    from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_router import (
        route_governed_workspace_creation_repository_bootstrap,
    )

    governed_workspace_creation = route_governed_workspace_creation_repository_bootstrap(
        raw, session_id=session_id
    )
    if governed_workspace_creation is not None:
        return governed_workspace_creation

    from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_router import (
        route_governed_code_generation_changeset_creation,
    )

    governed_code_generation = route_governed_code_generation_changeset_creation(
        raw, session_id=session_id
    )
    if governed_code_generation is not None:
        return governed_code_generation

    from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_router import (
        route_governed_git_delivery,
    )

    governed_git_delivery = route_governed_git_delivery(raw, session_id=session_id)
    if governed_git_delivery is not None:
        return governed_git_delivery

    from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_router import (
        route_governed_deployment_execution,
    )

    governed_deployment_execution = route_governed_deployment_execution(raw, session_id=session_id)
    if governed_deployment_execution is not None:
        return governed_deployment_execution

    from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_router import (
        route_governed_end_to_end_delivery_certification,
    )

    governed_end_to_end_delivery_certification = route_governed_end_to_end_delivery_certification(
        raw, session_id=session_id
    )
    if governed_end_to_end_delivery_certification is not None:
        return governed_end_to_end_delivery_certification

    from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_router import (
        route_real_world_delivery_proof_program,
    )

    real_world_delivery_proof = route_real_world_delivery_proof_program(raw, session_id=session_id)
    if real_world_delivery_proof is not None:
        return real_world_delivery_proof

    from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_router import (
        route_delivery_optimization_program,
    )

    delivery_optimization = route_delivery_optimization_program(raw, session_id=session_id)
    if delivery_optimization is not None:
        return delivery_optimization

    from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_router import (
        route_phase2_provider_execution_expansion_program,
    )

    phase2_provider_expansion = route_phase2_provider_execution_expansion_program(raw, session_id=session_id)
    if phase2_provider_expansion is not None:
        return phase2_provider_expansion

    from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_router import (
        route_multi_cloud_operational_proof_program,
    )

    multi_cloud_operational_proof = route_multi_cloud_operational_proof_program(raw, session_id=session_id)
    if multi_cloud_operational_proof is not None:
        return multi_cloud_operational_proof

    from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_router import (
        route_intelligence_performance_evidence_scalability_program,
    )

    intelligence_performance = route_intelligence_performance_evidence_scalability_program(raw, session_id=session_id)
    if intelligence_performance is not None:
        return intelligence_performance

    from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_router import (
        route_intelligence_runtime_optimization_program,
    )

    intelligence_runtime_optimization = route_intelligence_runtime_optimization_program(raw, session_id=session_id)
    if intelligence_runtime_optimization is not None:
        return intelligence_runtime_optimization

    from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_router import (
        route_intelligence_scalability_implementation_program,
    )

    intelligence_scalability_implementation = route_intelligence_scalability_implementation_program(
        raw, session_id=session_id
    )
    if intelligence_scalability_implementation is not None:
        return intelligence_scalability_implementation

    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_router import (
        route_compose_runtime_guardrails_program,
    )

    compose_runtime_guardrails = route_compose_runtime_guardrails_program(raw, session_id=session_id)
    if compose_runtime_guardrails is not None:
        return compose_runtime_guardrails

    from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_router import (
        route_first_customer_delivery_pilot_program,
    )

    first_customer_delivery_pilot = route_first_customer_delivery_pilot_program(raw, session_id=session_id)
    if first_customer_delivery_pilot is not None:
        return first_customer_delivery_pilot

    from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_router import (
        route_customer_value_adoption_validation_program,
    )

    customer_value_adoption_validation = route_customer_value_adoption_validation_program(
        raw, session_id=session_id
    )
    if customer_value_adoption_validation is not None:
        return customer_value_adoption_validation

    from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_router import (
        route_multi_customer_value_proof_program,
    )

    multi_customer_value_proof = route_multi_customer_value_proof_program(raw, session_id=session_id)
    if multi_customer_value_proof is not None:
        return multi_customer_value_proof

    from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_router import (
        route_customer_scale_validation_program,
    )

    customer_scale_validation = route_customer_scale_validation_program(raw, session_id=session_id)
    if customer_scale_validation is not None:
        return customer_scale_validation

    from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_router import (
        route_commercial_validation_program,
    )

    commercial_validation = route_commercial_validation_program(raw, session_id=session_id)
    if commercial_validation is not None:
        return commercial_validation

    from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_router import (
        route_unit_economics_business_sustainability_program,
    )

    unit_economics_business_sustainability = route_unit_economics_business_sustainability_program(
        raw, session_id=session_id
    )
    if unit_economics_business_sustainability is not None:
        return unit_economics_business_sustainability

    from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_router import (
        route_business_operating_model_validation_program,
    )

    business_operating_model_validation = route_business_operating_model_validation_program(
        raw, session_id=session_id
    )
    if business_operating_model_validation is not None:
        return business_operating_model_validation

    from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_router import (
        route_real_evidence_density_trust_maturity_program,
    )

    real_evidence_density_trust_maturity = route_real_evidence_density_trust_maturity_program(
        raw, session_id=session_id
    )
    if real_evidence_density_trust_maturity is not None:
        return real_evidence_density_trust_maturity

    from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_router import (
        route_real_usage_density_platform_adoption_program,
    )

    real_usage_density_platform_adoption = route_real_usage_density_platform_adoption_program(
        raw, session_id=session_id
    )
    if real_usage_density_platform_adoption is not None:
        return real_usage_density_platform_adoption

    from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_router import (
        route_revenue_density_business_viability_program,
    )

    revenue_density_business_viability = route_revenue_density_business_viability_program(
        raw, session_id=session_id
    )
    if revenue_density_business_viability is not None:
        return revenue_density_business_viability

    from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_router import (
        route_enterprise_platform_maturity_readiness_audit_program,
    )

    enterprise_platform_maturity_readiness_audit = route_enterprise_platform_maturity_readiness_audit_program(
        raw, session_id=session_id
    )
    if enterprise_platform_maturity_readiness_audit is not None:
        return enterprise_platform_maturity_readiness_audit

    from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_router import (
        route_strategic_direction_next_growth_decision_program,
    )

    strategic_direction_next_growth = route_strategic_direction_next_growth_decision_program(
        raw, session_id=session_id
    )
    if strategic_direction_next_growth is not None:
        return strategic_direction_next_growth

    from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_router import (
        route_governed_strategic_execution_program,
    )

    governed_strategic_execution = route_governed_strategic_execution_program(
        raw, session_id=session_id
    )
    if governed_strategic_execution is not None:
        return governed_strategic_execution

    from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_router import (
        route_strategic_execution_oversight_outcome_governance_program,
    )

    strategic_execution_oversight = route_strategic_execution_oversight_outcome_governance_program(
        raw, session_id=session_id
    )
    if strategic_execution_oversight is not None:
        return strategic_execution_oversight

    from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_router import (
        route_autonomous_execution_maturity_program,
    )

    autonomous_execution_maturity = route_autonomous_execution_maturity_program(
        raw, session_id=session_id
    )
    if autonomous_execution_maturity is not None:
        return autonomous_execution_maturity

    from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_router import (
        route_governed_autonomous_execution_proof_program,
    )

    governed_autonomous_execution_proof = route_governed_autonomous_execution_proof_program(
        raw, session_id=session_id
    )
    if governed_autonomous_execution_proof is not None:
        return governed_autonomous_execution_proof

    from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_router import (
        route_governed_autonomous_operations_certification_program,
    )

    governed_autonomous_operations_certification = route_governed_autonomous_operations_certification_program(
        raw, session_id=session_id
    )
    if governed_autonomous_operations_certification is not None:
        return governed_autonomous_operations_certification

    from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_router import (
        route_production_reality_longitudinal_operations_program,
    )

    production_reality_longitudinal_operations = route_production_reality_longitudinal_operations_program(
        raw, session_id=session_id
    )
    if production_reality_longitudinal_operations is not None:
        return production_reality_longitudinal_operations

    from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_router import (
        route_real_world_comparative_performance_program,
    )

    real_world_comparative_performance = route_real_world_comparative_performance_program(
        raw, session_id=session_id
    )
    if real_world_comparative_performance is not None:
        return real_world_comparative_performance

    from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_router import (
        route_compounding_value_continuous_improvement_program,
    )

    compounding_value_continuous_improvement = route_compounding_value_continuous_improvement_program(
        raw, session_id=session_id
    )
    if compounding_value_continuous_improvement is not None:
        return compounding_value_continuous_improvement

    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_router import (
        route_multi_repository_engineering_intelligence,
    )

    multi_repository_engineering_intelligence = route_multi_repository_engineering_intelligence(
        raw, session_id=session_id
    )
    if multi_repository_engineering_intelligence is not None:
        return multi_repository_engineering_intelligence

    from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_router import (
        route_cross_repository_product_evolution_intelligence,
    )

    cross_repository_product_evolution_intelligence = route_cross_repository_product_evolution_intelligence(
        raw, session_id=session_id
    )
    if cross_repository_product_evolution_intelligence is not None:
        return cross_repository_product_evolution_intelligence

    from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_router import (
        route_autonomous_product_stewardship,
    )

    autonomous_product_stewardship = route_autonomous_product_stewardship(raw, session_id=session_id)
    if autonomous_product_stewardship is not None:
        return autonomous_product_stewardship

    from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_router import (
        route_autonomous_application_lifecycle_management,
    )

    autonomous_application_lifecycle_management = route_autonomous_application_lifecycle_management(
        raw, session_id=session_id
    )
    if autonomous_application_lifecycle_management is not None:
        return autonomous_application_lifecycle_management

    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_router import (
        route_autonomous_business_operating_system,
    )

    autonomous_business_operating_system = route_autonomous_business_operating_system(
        raw, session_id=session_id
    )
    if autonomous_business_operating_system is not None:
        return autonomous_business_operating_system

    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_router import (
        route_capability_registry_runtime_integration,
    )

    capability_registry_runtime_integration = route_capability_registry_runtime_integration(
        raw, session_id=session_id
    )
    if capability_registry_runtime_integration is not None:
        return capability_registry_runtime_integration

    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_router import (
        route_autonomous_capability_registry,
    )

    autonomous_capability_registry = route_autonomous_capability_registry(raw, session_id=session_id)
    if autonomous_capability_registry is not None:
        return autonomous_capability_registry

    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_router import (
        route_multi_tenant_platform_foundation,
    )

    multi_tenant_platform_foundation = route_multi_tenant_platform_foundation(raw, session_id=session_id)
    if multi_tenant_platform_foundation is not None:
        return multi_tenant_platform_foundation

    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_router import (
        route_tenant_onboarding_activation,
    )

    tenant_onboarding_activation = route_tenant_onboarding_activation(raw, session_id=session_id)
    if tenant_onboarding_activation is not None:
        return tenant_onboarding_activation

    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_router import (
        route_identity_access_hardening,
    )

    identity_access_hardening = route_identity_access_hardening(raw, session_id=session_id)
    if identity_access_hardening is not None:
        return identity_access_hardening

    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_router import (
        route_provider_connection_experience,
    )

    provider_connection_experience = route_provider_connection_experience(raw, session_id=session_id)
    if provider_connection_experience is not None:
        return provider_connection_experience

    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_router import (
        route_channel_integration_foundation,
    )

    channel_integration_foundation = route_channel_integration_foundation(raw, session_id=session_id)
    if channel_integration_foundation is not None:
        return channel_integration_foundation

    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_router import (
        route_billing_entitlements_foundation,
    )

    billing_entitlements_foundation = route_billing_entitlements_foundation(raw, session_id=session_id)
    if billing_entitlements_foundation is not None:
        return billing_entitlements_foundation

    from aethos_core.mission_control.customer_administration_console.customer_administration_console_router import (
        route_customer_administration_console,
    )

    customer_administration_console = route_customer_administration_console(raw, session_id=session_id)
    if customer_administration_console is not None:
        return customer_administration_console

    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_router import (
        route_customer_usage_audit_portal,
    )

    customer_usage_audit_portal = route_customer_usage_audit_portal(raw, session_id=session_id)
    if customer_usage_audit_portal is not None:
        return customer_usage_audit_portal

    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_router import (
        route_payment_integration_readiness,
    )

    payment_integration_readiness = route_payment_integration_readiness(raw, session_id=session_id)
    if payment_integration_readiness is not None:
        return payment_integration_readiness

    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_router import (
        route_saas_launch_readiness_assessment,
    )

    saas_launch_readiness_assessment = route_saas_launch_readiness_assessment(raw, session_id=session_id)
    if saas_launch_readiness_assessment is not None:
        return saas_launch_readiness_assessment

    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_router import (
        route_customer_support_success_foundation,
    )

    customer_support_success_foundation = route_customer_support_success_foundation(raw, session_id=session_id)
    if customer_support_success_foundation is not None:
        return customer_support_success_foundation

    from aethos_core.mission_control.public_product_experience.public_product_experience_router import (
        route_public_product_experience,
    )

    public_product_experience = route_public_product_experience(raw, session_id=session_id)
    if public_product_experience is not None:
        return public_product_experience

    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_router import (
        route_limited_beta_launch_program,
    )

    limited_beta_launch_program = route_limited_beta_launch_program(raw, session_id=session_id)
    if limited_beta_launch_program is not None:
        return limited_beta_launch_program

    from aethos_core.mission_control.launch_operations_center.launch_operations_center_router import (
        route_launch_operations_center,
    )

    launch_operations_center = route_launch_operations_center(raw, session_id=session_id)
    if launch_operations_center is not None:
        return launch_operations_center

    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_router import (
        route_public_launch_readiness_freeze,
    )

    public_launch_readiness_freeze = route_public_launch_readiness_freeze(raw, session_id=session_id)
    if public_launch_readiness_freeze is not None:
        return public_launch_readiness_freeze

    from aethos_core.mission_control.launch_decision_package.launch_decision_package_router import (
        route_launch_decision_package,
    )

    launch_decision_package = route_launch_decision_package(raw, session_id=session_id)
    if launch_decision_package is not None:
        return launch_decision_package

    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_router import (
        route_post_launch_operations_baseline,
    )

    post_launch_operations_baseline = route_post_launch_operations_baseline(raw, session_id=session_id)
    if post_launch_operations_baseline is not None:
        return post_launch_operations_baseline

    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_router import (
        route_continuous_product_improvement,
    )

    continuous_product_improvement = route_continuous_product_improvement(raw, session_id=session_id)
    if continuous_product_improvement is not None:
        return continuous_product_improvement

    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_router import (
        route_product_analytics_foundation,
    )

    product_analytics_foundation = route_product_analytics_foundation(raw, session_id=session_id)
    if product_analytics_foundation is not None:
        return product_analytics_foundation

    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_router import (
        route_customer_feedback_intelligence,
    )

    customer_feedback_intelligence = route_customer_feedback_intelligence(raw, session_id=session_id)
    if customer_feedback_intelligence is not None:
        return customer_feedback_intelligence

    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_router import (
        route_growth_adoption_intelligence,
    )

    growth_adoption_intelligence = route_growth_adoption_intelligence(raw, session_id=session_id)
    if growth_adoption_intelligence is not None:
        return growth_adoption_intelligence

    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_router import (
        route_customer_journey_intelligence,
    )

    customer_journey_intelligence = route_customer_journey_intelligence(raw, session_id=session_id)
    if customer_journey_intelligence is not None:
        return customer_journey_intelligence

    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_router import (
        route_product_market_fit_intelligence,
    )

    product_market_fit_intelligence = route_product_market_fit_intelligence(raw, session_id=session_id)
    if product_market_fit_intelligence is not None:
        return product_market_fit_intelligence

    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_router import (
        route_customer_value_realization_intelligence,
    )

    customer_value_realization_intelligence = route_customer_value_realization_intelligence(raw, session_id=session_id)
    if customer_value_realization_intelligence is not None:
        return customer_value_realization_intelligence

    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_router import (
        route_strategic_portfolio_intelligence,
    )

    strategic_portfolio_intelligence = route_strategic_portfolio_intelligence(raw, session_id=session_id)
    if strategic_portfolio_intelligence is not None:
        return strategic_portfolio_intelligence

    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_router import (
        route_executive_decision_intelligence,
    )

    executive_decision_intelligence = route_executive_decision_intelligence(raw, session_id=session_id)
    if executive_decision_intelligence is not None:
        return executive_decision_intelligence

    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_router import (
        route_strategic_planning_intelligence,
    )

    strategic_planning_intelligence = route_strategic_planning_intelligence(raw, session_id=session_id)
    if strategic_planning_intelligence is not None:
        return strategic_planning_intelligence

    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_router import (
        route_enterprise_program_intelligence,
    )

    enterprise_program_intelligence = route_enterprise_program_intelligence(raw, session_id=session_id)
    if enterprise_program_intelligence is not None:
        return enterprise_program_intelligence

    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_router import (
        route_organizational_effectiveness_intelligence,
    )

    organizational_effectiveness_intelligence = route_organizational_effectiveness_intelligence(
        raw, session_id=session_id
    )
    if organizational_effectiveness_intelligence is not None:
        return organizational_effectiveness_intelligence

    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_router import (
        route_enterprise_operating_review_intelligence,
    )

    enterprise_operating_review_intelligence = route_enterprise_operating_review_intelligence(
        raw, session_id=session_id
    )
    if enterprise_operating_review_intelligence is not None:
        return enterprise_operating_review_intelligence

    from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_router import (
        route_executive_operating_system_dashboard,
    )

    executive_operating_system_dashboard = route_executive_operating_system_dashboard(
        raw, session_id=session_id
    )
    if executive_operating_system_dashboard is not None:
        return executive_operating_system_dashboard

    bounded_execution_participation = route_bounded_execution_participation(raw, session_id=session_id)
    if bounded_execution_participation is not None:
        return bounded_execution_participation
    mission_authorization = route_mission_authorization(raw, session_id=session_id)
    if mission_authorization is not None:
        return mission_authorization
    work_package_readiness_lane_admission = route_work_package_readiness_lane_admission(raw, session_id=session_id)
    if work_package_readiness_lane_admission is not None:
        return work_package_readiness_lane_admission
    bounded_delivery_work_packages = route_bounded_delivery_work_packages(raw, session_id=session_id)
    if bounded_delivery_work_packages is not None:
        return bounded_delivery_work_packages
    execution_handoff_coordination = route_execution_handoff_coordination(raw, session_id=session_id)
    if execution_handoff_coordination is not None:
        return execution_handoff_coordination
    human_decision_board = route_human_decision_board(raw, session_id=session_id)
    if human_decision_board is not None:
        return human_decision_board
    mission_planning_deliberation = route_mission_planning_deliberation(raw, session_id=session_id)
    if mission_planning_deliberation is not None:
        return mission_planning_deliberation
    mission_planning = route_mission_planning(raw, session_id=session_id)
    if mission_planning is not None:
        return mission_planning
    constitutional_synthesis = route_constitutional_synthesis(raw, session_id=session_id)
    if constitutional_synthesis is not None:
        return constitutional_synthesis
    constitutional_pluralism = route_constitutional_pluralism(raw, session_id=session_id)
    if constitutional_pluralism is not None:
        return constitutional_pluralism
    constitutional_legitimacy = route_constitutional_legitimacy(raw, session_id=session_id)
    if constitutional_legitimacy is not None:
        return constitutional_legitimacy
    constitutional_audit = route_constitutional_audit(raw, session_id=session_id)
    if constitutional_audit is not None:
        return constitutional_audit
    constitutional_ethics = route_constitutional_ethics(raw, session_id=session_id)
    if constitutional_ethics is not None:
        return constitutional_ethics
    institutional_existential_risk = route_institutional_existential_risk(raw, session_id=session_id)
    if institutional_existential_risk is not None:
        return institutional_existential_risk
    institutional_external_relations = route_institutional_external_relations(raw, session_id=session_id)
    if institutional_external_relations is not None:
        return institutional_external_relations
    institutional_identity = route_institutional_identity(raw, session_id=session_id)
    if institutional_identity is not None:
        return institutional_identity
    governance_evolution = route_governance_evolution(raw, session_id=session_id)
    if governance_evolution is not None:
        return governance_evolution
    governance_resilience = route_governance_resilience(raw, session_id=session_id)
    if governance_resilience is not None:
        return governance_resilience
    governance_coherence = route_governance_coherence(raw, session_id=session_id)
    if governance_coherence is not None:
        return governance_coherence
    governance_policy_interpretation = route_governance_policy_interpretation(raw, session_id=session_id)
    if governance_policy_interpretation is not None:
        return governance_policy_interpretation
    governance_doctrine = route_governance_doctrine(raw, session_id=session_id)
    if governance_doctrine is not None:
        return governance_doctrine
    governance_role_architecture = route_governance_role_architecture(raw, session_id=session_id)
    if governance_role_architecture is not None:
        return governance_role_architecture
    governance_collaboration = route_governance_collaboration(raw, session_id=session_id)
    if governance_collaboration is not None:
        return governance_collaboration
    governance_deliberation = route_governance_deliberation(raw, session_id=session_id)
    if governance_deliberation is not None:
        return governance_deliberation
    mission_readiness_review = route_mission_readiness_review(raw, session_id=session_id)
    if mission_readiness_review is not None:
        return mission_readiness_review
    mission_orchestration = route_mission_orchestration(raw, session_id=session_id)
    if mission_orchestration is not None:
        return mission_orchestration
    mission_strategy = route_mission_strategy(raw, session_id=session_id)
    if mission_strategy is not None:
        return mission_strategy
    governance_simulation = route_governance_simulation(raw, session_id=session_id)
    if governance_simulation is not None:
        return governance_simulation
    governance_insights = route_governance_insights(raw, session_id=session_id)
    if governance_insights is not None:
        return governance_insights
    operator_guidance = route_operator_guidance(raw, session_id=session_id)
    if operator_guidance is not None:
        return operator_guidance
    knowledge_spaces = route_knowledge_spaces(raw, session_id=session_id)
    if knowledge_spaces is not None:
        return knowledge_spaces
    cross_session_memory = route_cross_session_operational_memory(raw, session_id=session_id)
    if cross_session_memory is not None:
        return cross_session_memory
    operational_memory = route_operational_memory(raw, session_id=session_id)
    if operational_memory is not None:
        return operational_memory
    rerun_plan = route_governed_rerun_plan(raw, session_id=session_id)
    if rerun_plan is not None:
        return rerun_plan
    if not is_mission_control_observability_intent(raw):
        return None

    if "search" in raw.lower() and "audit" in raw.lower():
        query = raw.split("audit", 1)[-1].strip() if "audit" in raw.lower() else ""
        result = search_mission_control_audit(session_id=session_id, query=query)
        body = render_audit_search(result.snapshot) if result.ok else "Audit search unavailable."
        return body, "mission_control_audit_search", _meta(
            session_id, stage="audit_search", correlation_id=str(result.snapshot.get("correlation_id") or "")
        )

    result = build_mission_control_snapshot(session_id=session_id)
    if not result.ok:
        body = f"Mission Control snapshot blocked: {', '.join(result.blockers)}"
        return body, "mission_control_snapshot_blocked", _meta(session_id, stage="blocked")

    snap = result.snapshot
    if "attention" in raw.lower() and "queue" in raw.lower():
        body = render_attention_queue(snap)
        intent = "mission_control_attention_queue"
        stage = "attention_queue"
    elif "health" in raw.lower():
        body = render_health_summary(snap)
        intent = "mission_control_health_summary"
        stage = "health_summary"
    elif "timeline" in raw.lower():
        body = render_timeline(snap)
        intent = "mission_control_unified_timeline"
        stage = "unified_timeline"
    else:
        body = render_snapshot(snap)
        intent = "mission_control_snapshot"
        stage = "snapshot"

    return body, intent, _meta(
        session_id,
        stage=stage,
        correlation_id=str(snap.get("correlation_id") or ""),
        snapshot_id=str(snap.get("snapshot_id") or ""),
    )
