# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — chat router for repository knowledge graph."""

from __future__ import annotations

from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_contract import (
    CODE_MODIFICATION_AUTHORITY_FIX_240,
    CROSS_REPO_AUTHORITY_FIX_240,
    DEPLOY_AUTHORITY_FIX_240,
    GATE_BYPASS_ENABLED_FIX_240,
    KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
    MERGE_AUTHORITY_FIX_240,
    MUTATION_PERFORMED_FIX_240,
    REPOSITORY_AUTHORITY_FIX_240,
    REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID,
    ROLLBACK_AUTHORITY_FIX_240,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_intent import (
    is_repository_knowledge_graph_intent,
    parse_repository_knowledge_graph_record_intent,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_renderer import (
    render_repository_knowledge_graph,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_service import (
    build_repository_knowledge_graph,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_store import (
    append_repository_knowledge_graph_record,
)
from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session


def _resolve_repository_id(session_id: str) -> str | None:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    repo = str((pr_open or {}).get("repository") or "")
    if repo:
        return repo
    issue_ref = str((plan or {}).get("issue_reference") or "")
    if issue_ref:
        return issue_ref.split("#")[0] if "#" in issue_ref else issue_ref
    return None


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID,
        "matched_module": (
            "mission_control.repository_knowledge_graph.repository_knowledge_graph_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_240 is False else "true",
        "repository_authority": "false" if REPOSITORY_AUTHORITY_FIX_240 is False else "true",
        "code_modification_authority": "false"
        if CODE_MODIFICATION_AUTHORITY_FIX_240 is False
        else "true",
        "cross_repo_authority": "false" if CROSS_REPO_AUTHORITY_FIX_240 is False else "true",
        "knowledge_graph_execution": "false"
        if KNOWLEDGE_GRAPH_EXECUTION_FIX_240 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_240 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_240 is False else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_240 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_240 is False else "true",
        "mutation_scope": "repository_knowledge_graph",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "intelligence_not_authority",
        **extra,
    }


def route_repository_knowledge_graph(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_repository_knowledge_graph_record_intent(text)
    if record_intent is not None:
        kind, content, metadata = record_intent
        repository_id = _resolve_repository_id(session_id)
        record, blockers = append_repository_knowledge_graph_record(
            session_id=session_id,
            kind=kind,
            content=content,
            repository_id=repository_id,
            metadata=metadata,
        )
        if blockers or not record:
            body = f"Repository knowledge graph record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_repository_knowledge_graph_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Repository intelligence record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "repository_intelligence ≠ repository_authority."
        )
        return (
            body,
            "mission_control_repository_knowledge_graph_record",
            _meta(session_id, stage="repository_memory", record_id=str(record.get("record_id") or "")),
        )

    if not is_repository_knowledge_graph_intent(text):
        return None

    result = build_repository_knowledge_graph(session_id=session_id)
    body = render_repository_knowledge_graph(result.repository_knowledge_graph)
    return (
        body,
        "mission_control_repository_knowledge_graph",
        _meta(session_id, stage="repository_knowledge_graph"),
    )
