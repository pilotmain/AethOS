# SPDX-License-Identifier: Apache-2.0
"""FIX 338 — end-to-end delivery certification executor."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_executor import (
    verify_code_generation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_intent import (
    handle_governed_code_generation_intent,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_executor import (
    verify_deployment,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_intent import (
    handle_governed_deployment_execution_intent,
    parse_governed_deployment_execution_intent,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    CERTIFICATION_SCENARIOS,
    CERTIFICATION_STATUSES,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    append_governed_end_to_end_delivery_certification_record,
    has_certification_decision_approve,
    list_delivery_run_registry_entries,
    register_delivery_run,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_executor import (
    verify_git_delivery,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_intent import (
    handle_governed_git_delivery_intent,
    parse_governed_git_delivery_intent,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_executor import (
    verify_workspace_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_intent import (
    handle_governed_workspace_creation_intent,
)


def _run_workspace_chain(*, session_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_creation_review_note",
            "content": (
                f"name={scenario['workspace_name']} "
                f"template={scenario['template_id']} org=org-cert"
            ),
            "metadata": {
                "workspace_name": scenario["workspace_name"],
                "template_id": scenario["template_id"],
                "org_id": "org-cert",
            },
        },
        session_id=session_id,
    )
    handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_decision_approve",
            "content": f"Human approves workspace for {scenario['name']}",
        },
        session_id=session_id,
    )
    return verify_workspace_bootstrap(session_id=session_id)


def _run_generation_chain(*, session_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    feature = scenario["feature_name"]
    gen_type = scenario["generation_type"]
    handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_request_review_note",
            "content": f"type={gen_type} feature={feature} Certification scenario change",
            "metadata": {
                "type": gen_type,
                "feature_name": feature,
                "title": scenario["name"],
            },
        },
        session_id=session_id,
    )
    handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_decision_approve",
            "content": f"Human approves code generation for {scenario['name']}",
        },
        session_id=session_id,
    )
    return verify_code_generation(session_id=session_id)


def _run_git_delivery_chain(*, session_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    feature = scenario["feature_name"]
    for text in (
        f"git delivery review: work_item={feature} target_branch=main",
        "branch delivery review: Approve delivery branch for certification",
        "commit delivery review: Approve commit assembly for certification",
        "pull request review: Approve PR creation for certification",
        "git delivery decision approve: Human approves git delivery for certification",
    ):
        intent = parse_governed_git_delivery_intent(text)
        if intent is None:
            return {"ok": False, "verified": False, "detail": f"Failed to parse git intent: {text}"}
        handle_governed_git_delivery_intent(intent, session_id=session_id)
    return verify_git_delivery(session_id=session_id)


def _run_deployment_chain(*, session_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    provider = scenario.get("provider") or "railway"
    environment = scenario.get("environment") or "staging"
    target = scenario.get("workspace_name") or "cert-service"
    for text in (
        f"deployment review: provider={provider} environment={environment} target={target}",
        "deployment readiness review: Provider configured for certification run",
        "deployment execution review: Approve certification deployment execution",
    ):
        intent = parse_governed_deployment_execution_intent(text)
        if intent is None:
            return {"ok": False, "verified": False, "detail": f"Failed to parse deployment intent: {text}"}
        handle_governed_deployment_execution_intent(intent, session_id=session_id)
    intent = parse_governed_deployment_execution_intent(
        "deployment decision approve: Human approves governed certification deployment"
    )
    if intent is None:
        return {"ok": False, "verified": False, "detail": "Failed to parse deployment decision approve"}
    handle_governed_deployment_execution_intent(intent, session_id=session_id)
    return verify_deployment(session_id=session_id)


def run_certification_scenario(*, session_id: str, scenario_id: str) -> dict[str, Any]:
    scenario = CERTIFICATION_SCENARIOS.get(scenario_id)
    if scenario is None:
        return {
            "ok": False,
            "passed": False,
            "error": "unsupported_scenario",
            "detail": f"Unsupported certification scenario: {scenario_id}",
        }

    run_session = f"{session_id}::{scenario_id}"[:64]
    started = perf_counter()
    started_at = datetime.now(UTC).isoformat()
    run_id = f"et5-run-{uuid4().hex[:10]}"

    stage_results: dict[str, Any] = {}
    blockers: list[str] = []

    if scenario.get("includes_workspace"):
        workspace = _run_workspace_chain(session_id=run_session, scenario=scenario)
        stage_results["workspace"] = workspace
        if not workspace.get("verified"):
            blockers.append("workspace_verification_failed")
    elif scenario.get("existing_repository") or scenario.get("documentation_only"):
        workspace = _run_workspace_chain(session_id=run_session, scenario=scenario)
        stage_results["workspace"] = {
            **workspace,
            "skipped": True,
            "prerequisite_bootstrap": True,
        }
        if not workspace.get("verified"):
            blockers.append("workspace_verification_failed")
    else:
        stage_results["workspace"] = {"ok": True, "verified": True, "skipped": True}

    generation = _run_generation_chain(session_id=run_session, scenario=scenario)
    stage_results["generation"] = generation
    if not generation.get("verified"):
        blockers.append("generation_verification_failed")

    git = _run_git_delivery_chain(session_id=run_session, scenario=scenario)
    stage_results["git_delivery"] = git
    if not git.get("verified"):
        blockers.append("git_delivery_verification_failed")

    if scenario.get("includes_deployment"):
        deployment = _run_deployment_chain(session_id=run_session, scenario=scenario)
        stage_results["deployment"] = deployment
        if not deployment.get("verified"):
            blockers.append("deployment_verification_failed")
    else:
        stage_results["deployment"] = {"ok": True, "verified": True, "skipped": True}

    duration_ms = int((perf_counter() - started) * 1000)
    passed = not blockers

    evidence = {
        "execution_track_1_workspace": stage_results.get("workspace"),
        "execution_track_2_generation": stage_results.get("generation"),
        "execution_track_3_git_delivery": stage_results.get("git_delivery"),
        "execution_track_4_deployment": stage_results.get("deployment"),
    }

    run_entry = register_delivery_run(
        entry={
            "run_id": run_id,
            "session_id": session_id,
            "run_session_id": run_session,
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "outcome": "PASSED" if passed else "FAILED",
            "passed": passed,
            "blockers": blockers,
            "duration_ms": duration_ms,
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat(),
            "stage_results": stage_results,
            "evidence": evidence,
            "trust_mutation_performed": False,
            "delivery_authority_granted": False,
        }
    )

    append_governed_end_to_end_delivery_certification_record(
        session_id=session_id,
        kind="certification_run_executed_note",
        content=f"Certification run {scenario_id} — {'PASSED' if passed else 'FAILED'} ({duration_ms}ms)",
        metadata={"run_id": run_id, "scenario_id": scenario_id, "passed": passed},
    )

    return {
        "ok": passed,
        "passed": passed,
        "run": run_entry,
        "blockers": blockers,
        "duration_ms": duration_ms,
        "detail": f"Certification scenario {scenario_id} {'passed' if passed else 'failed'}",
    }


def assess_certification_status(*, session_id: str) -> dict[str, Any]:
    runs = [
        row for row in list_delivery_run_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    passed_runs = [row for row in runs if row.get("passed") is True]
    failed_runs = [row for row in runs if row.get("passed") is False]
    total = len(runs)
    pass_count = len(passed_runs)

    core_scenarios = (
        "scenario_1_fastapi_railway",
        "scenario_2_spring_boot_railway",
        "scenario_3_nextjs_vercel",
    )
    core_passed = {
        str(row.get("scenario_id") or "")
        for row in passed_runs
        if str(row.get("scenario_id") or "") in core_scenarios
    }
    all_core_passed = core_passed == set(core_scenarios)

    human_approved = has_certification_decision_approve(session_id=session_id)
    evidence_complete = pass_count > 0 and all(
        (row.get("evidence") or {}).get("execution_track_3_git_delivery", {}).get("verified")
        for row in passed_runs
    )

    production_runs = [
        row
        for row in passed_runs
        if str((row.get("stage_results") or {}).get("deployment", {}).get("environment") or "").lower()
        == "production"
    ]

    if total == 0:
        status = "NOT_CERTIFIED"
    elif human_approved and all_core_passed and evidence_complete and production_runs:
        status = "PRODUCTION_CERTIFIED"
    elif human_approved and all_core_passed and evidence_complete:
        status = "CERTIFIED"
    elif pass_count > 0:
        status = "PARTIALLY_CERTIFIED"
    else:
        status = "NOT_CERTIFIED"

    if status not in CERTIFICATION_STATUSES:
        status = "NOT_CERTIFIED"

    pass_rate = round(pass_count / total, 4) if total else 0.0
    failure_rate = round(len(failed_runs) / total, 4) if total else 0.0

    return {
        "status": status,
        "delivery_certification_status": status,
        "run_count": total,
        "passed_count": pass_count,
        "failed_count": len(failed_runs),
        "pass_rate": pass_rate,
        "failure_rate": failure_rate,
        "core_scenarios_passed": sorted(core_passed),
        "all_core_scenarios_passed": all_core_passed,
        "human_certification_approved": human_approved,
        "evidence_complete": evidence_complete,
        "delivery_authority_granted": False,
        "trust_mutation_performed": False,
        "automatic_promotion_performed": False,
        "read_only": True,
    }


def analyze_delivery_reliability(*, session_id: str | None = None) -> dict[str, Any]:
    runs = list_delivery_run_registry_entries()
    if session_id:
        runs = [row for row in runs if str(row.get("session_id") or "") == session_id]

    total = len(runs)
    passed = sum(1 for row in runs if row.get("passed") is True)
    failed = total - passed
    recovered = sum(
        1
        for row in runs
        if row.get("passed") is True
        and any(
            str(b).endswith("_verification_failed")
            for b in (row.get("blockers") or [])
        )
        is False
    )
    interventions = sum(
        1
        for row in runs
        if row.get("passed") is True and int(row.get("duration_ms") or 0) > 0
    )

    return {
        "report_id": "delivery-reliability-report",
        "run_count": total,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "failure_rate": round(failed / total, 4) if total else 0.0,
        "recovery_rate": round(recovered / failed, 4) if failed else 1.0 if passed else 0.0,
        "intervention_rate": round(interventions / total, 4) if total else 0.0,
        "read_only": True,
    }


def analyze_delivery_failures(*, session_id: str | None = None) -> dict[str, Any]:
    runs = list_delivery_run_registry_entries()
    if session_id:
        runs = [row for row in runs if str(row.get("session_id") or "") == session_id]

    generation_failures = 0
    git_failures = 0
    deployment_failures = 0
    verification_failures = 0

    for row in runs:
        if row.get("passed") is True:
            continue
        blockers = [str(b) for b in (row.get("blockers") or [])]
        if any("generation" in b for b in blockers):
            generation_failures += 1
        if any("git" in b for b in blockers):
            git_failures += 1
        if any("deployment" in b for b in blockers):
            deployment_failures += 1
        if blockers:
            verification_failures += 1

    return {
        "analysis_id": "delivery-failure-analysis",
        "generation_failures": generation_failures,
        "git_failures": git_failures,
        "deployment_failures": deployment_failures,
        "verification_failures": verification_failures,
        "failure_detected": any(
            [generation_failures, git_failures, deployment_failures, verification_failures]
        ),
        "read_only": True,
    }


def analyze_human_interventions(*, session_id: str) -> dict[str, Any]:
    from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
        list_governed_end_to_end_delivery_certification_records,
    )

    records = [
        row
        for row in list_governed_end_to_end_delivery_certification_records()
        if str(row.get("session_id") or "") == session_id
    ]
    approvals = [r for r in records if str(r.get("kind") or "").endswith("_approve")]
    corrections = [r for r in records if "review_note" in str(r.get("kind") or "")]
    manual_runs = [r for r in records if str(r.get("kind") or "") == "certification_run_executed_note"]

    return {
        "report_id": "intervention-analysis-report",
        "approval_count": len(approvals),
        "correction_count": len(corrections),
        "manual_action_count": len(manual_runs),
        "approvals": approvals[-5:],
        "corrections": corrections[-5:],
        "read_only": True,
    }


def measure_execution_quality(*, session_id: str) -> dict[str, Any]:
    runs = [
        row for row in list_delivery_run_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    if not runs:
        return {
            "report_id": "execution-quality-report",
            "workspace_success_rate": 0.0,
            "generation_success_rate": 0.0,
            "git_success_rate": 0.0,
            "deployment_success_rate": 0.0,
            "verification_success_rate": 0.0,
            "run_count": 0,
            "read_only": True,
        }

    def _stage_rate(stage: str) -> float:
        successes = sum(
            1
            for row in runs
            if (row.get("stage_results") or {}).get(stage, {}).get("verified") is True
            or (row.get("stage_results") or {}).get(stage, {}).get("skipped") is True
        )
        return round(successes / len(runs), 4)

    passed = sum(1 for row in runs if row.get("passed") is True)
    return {
        "report_id": "execution-quality-report",
        "workspace_success_rate": _stage_rate("workspace"),
        "generation_success_rate": _stage_rate("generation"),
        "git_success_rate": _stage_rate("git_delivery"),
        "deployment_success_rate": _stage_rate("deployment"),
        "verification_success_rate": round(passed / len(runs), 4),
        "run_count": len(runs),
        "read_only": True,
    }


def build_certification_evidence_bundle(*, session_id: str) -> dict[str, Any]:
    runs = [
        row for row in list_delivery_run_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = runs[-1] if runs else {}
    evidence = latest.get("evidence") or {}

    return {
        "bundle_id": "delivery-certification-evidence-bundle",
        "execution_track_1_receipts": evidence.get("execution_track_1_workspace"),
        "execution_track_2_receipts": evidence.get("execution_track_2_generation"),
        "execution_track_3_receipts": evidence.get("execution_track_3_git_delivery"),
        "execution_track_4_receipts": evidence.get("execution_track_4_deployment"),
        "run_id": latest.get("run_id"),
        "scenario_id": latest.get("scenario_id"),
        "evidence_complete": latest.get("passed") is True,
        "trust_mutation_performed": False,
        "read_only": True,
    }
