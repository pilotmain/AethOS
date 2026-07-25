# SPDX-License-Identifier: Apache-2.0
"""Structured operational evidence — provider-agnostic shape for execution artifacts."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact

CONFIDENCE_CONFIRMED = "confirmed"
CONFIDENCE_LIKELY = "likely"
CONFIDENCE_POSSIBLE = "possible"
CONFIDENCE_INSUFFICIENT = "insufficient_evidence"

_FAILED_STATES = frozenset({"error", "failed", "canceled", "cancelled"})


def evidence_item(
    *,
    source: str,
    type: str,
    confidence: str,
    message: str,
    at: str | float | None = None,
    **extra: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "source": source,
        "type": type,
        "confidence": confidence,
        "message": message,
    }
    if at is not None:
        item["at"] = at
    item.update(extra)
    return item


def append_evidence(artifact: ExecutionArtifact, item: dict[str, Any]) -> None:
    artifact.evidence.append(item)


def append_operational_event(
    artifact: ExecutionArtifact,
    *,
    label: str,
    source: str,
    at: str | float | None = None,
    **extra: Any,
) -> None:
    event: dict[str, Any] = {"label": label, "source": source}
    if at is not None:
        event["at"] = at
    event.update(extra)
    artifact.operational_events.append(event)


def select_failed_deployment(deployments: list[Any]) -> dict[str, Any] | None:
    for dep in deployments:
        if isinstance(dep, dict) and str(dep.get("state") or "").lower() in _FAILED_STATES:
            return dep
    for dep in deployments:
        if isinstance(dep, dict):
            return dep
    return None


def _deployment_state_confidence(state: str) -> str:
    low = (state or "").lower()
    if low in _FAILED_STATES:
        return CONFIDENCE_CONFIRMED
    if low in ("ready", "building"):
        return CONFIDENCE_LIKELY
    return CONFIDENCE_POSSIBLE


def evidence_from_deployment(dep: dict[str, Any], *, source: str = "vercel_api") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    state = str(dep.get("state") or "unknown")
    dep_id = str(dep.get("id") or "")
    conf = _deployment_state_confidence(state)
    items.append(
        evidence_item(
            source=source,
            type="deployment_state",
            confidence=conf,
            message=f"Deployment `{dep_id[:12] or 'unknown'}` state: {state} · target: {dep.get('target', 'unknown')}",
            deployment_id=dep_id,
            state=state,
            target=dep.get("target"),
            branch=dep.get("branch"),
            commit=dep.get("commit"),
            at=dep.get("created_at"),
        )
    )
    if dep.get("error_message"):
        items.append(
            evidence_item(
                source=source,
                type="failure_reason",
                confidence=CONFIDENCE_CONFIRMED,
                message=str(dep["error_message"])[:500],
                deployment_id=dep_id,
                at=dep.get("ready_at") or dep.get("created_at"),
            )
        )
    if dep.get("commit_message"):
        items.append(
            evidence_item(
                source=source,
                type="commit_context",
                confidence=CONFIDENCE_LIKELY,
                message=str(dep["commit_message"])[:240],
                deployment_id=dep_id,
                branch=dep.get("branch"),
                commit=dep.get("commit"),
            )
        )
    return items


def operational_events_from_deployment(dep: dict[str, Any], *, source: str = "vercel_api") -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    dep_id = str(dep.get("id") or "")
    if dep.get("created_at"):
        events.append(
            {
                "at": dep.get("created_at"),
                "label": "deployment created",
                "source": source,
                "deployment_id": dep_id,
            }
        )
    if dep.get("building_at"):
        events.append(
            {
                "at": dep.get("building_at"),
                "label": "build started",
                "source": source,
                "deployment_id": dep_id,
            }
        )
    state = str(dep.get("state") or "").lower()
    if state in _FAILED_STATES:
        events.append(
            {
                "at": dep.get("ready_at") or dep.get("created_at"),
                "label": "deployment failed",
                "source": source,
                "deployment_id": dep_id,
                "state": state,
            }
        )
        if dep.get("error_message"):
            events.append(
                {
                    "at": dep.get("ready_at") or dep.get("created_at"),
                    "label": f"failure: {str(dep['error_message'])[:160]}",
                    "source": source,
                    "deployment_id": dep_id,
                }
            )
    elif state == "ready" and dep.get("ready_at"):
        events.append(
            {
                "at": dep.get("ready_at"),
                "label": "deployment ready",
                "source": source,
                "deployment_id": dep_id,
            }
        )
    return events


def evidence_from_log_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    source = str(payload.get("source") or "vercel_api")
    dep_id = str(payload.get("deployment_id") or "")
    event_count = int(payload.get("event_count") or 0)
    if event_count:
        items.append(
            evidence_item(
                source=source,
                type="deployment_events",
                confidence=CONFIDENCE_LIKELY if event_count else CONFIDENCE_POSSIBLE,
                message=f"Collected {event_count} deployment events from Vercel API.",
                deployment_id=dep_id,
            )
        )
    for ev in payload.get("events") or []:
        if not isinstance(ev, dict):
            continue
        text = str(ev.get("text") or ev.get("message") or "").strip()
        if not text:
            continue
        low = text.lower()
        conf = CONFIDENCE_CONFIRMED if any(k in low for k in ("error", "failed", "fail")) else CONFIDENCE_LIKELY
        items.append(
            evidence_item(
                source=source,
                type="deployment_event",
                confidence=conf,
                message=text[:500],
                deployment_id=dep_id,
                at=ev.get("created") or ev.get("createdAt"),
                event_type=ev.get("type"),
            )
        )
        if len(items) >= 12:
            break
    for line in payload.get("log_lines") or []:
        if not line:
            continue
        low = str(line).lower()
        if "error" in low or "failed" in low:
            items.append(
                evidence_item(
                    source=source,
                    type="deployment_event",
                    confidence=CONFIDENCE_CONFIRMED,
                    message=str(line)[:500],
                    deployment_id=dep_id,
                )
            )
            break
    return items


def operational_events_from_log_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    source = str(payload.get("source") or "vercel_api")
    dep_id = str(payload.get("deployment_id") or "")
    for ev in payload.get("events") or []:
        if not isinstance(ev, dict):
            continue
        text = str(ev.get("text") or ev.get("message") or "").strip()
        if not text:
            continue
        events.append(
            {
                "at": ev.get("created") or ev.get("createdAt"),
                "label": text[:200],
                "source": source,
                "deployment_id": dep_id,
                "event_type": ev.get("type"),
            }
        )
        if len(events) >= 20:
            break
    return events


def evidence_from_inventory_tags(tags: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for tag in tags:
        if not tag:
            continue
        conf = CONFIDENCE_LIKELY
        if "failed" in tag.lower():
            conf = CONFIDENCE_LIKELY
        items.append(
            evidence_item(
                source="memory",
                type="inventory_signal",
                confidence=conf,
                message=str(tag),
            )
        )
    return items


def evidence_from_reachability(result: dict[str, Any]) -> dict[str, Any] | None:
    if not result.get("url"):
        return None
    reachable = result.get("reachable")
    if reachable is True:
        conf = CONFIDENCE_CONFIRMED
        msg = str(result.get("summary") or f"URL reachable: {result.get('url')}")
    elif reachable is False:
        conf = CONFIDENCE_CONFIRMED
        msg = str(result.get("summary") or f"URL unreachable: {result.get('url')}")
    else:
        conf = CONFIDENCE_POSSIBLE
        msg = str(result.get("summary") or "URL reachability inconclusive.")
    return evidence_item(
        source="local_probe",
        type="url_reachability",
        confidence=conf,
        message=msg,
        url=result.get("url"),
        status_code=result.get("status_code"),
    )


def derive_diagnostic_assessment(
    *,
    failed_dep: dict[str, Any] | None,
    deploy_state: str,
    inventory_evidence: list[str],
    reachability: dict[str, Any] | None,
) -> tuple[str | None, str]:
    if failed_dep and failed_dep.get("error_message"):
        return str(failed_dep["error_message"])[:500], CONFIDENCE_CONFIRMED
    if failed_dep and str(failed_dep.get("state") or "").lower() in _FAILED_STATES:
        msg = (
            f"Latest deployment `{str(failed_dep.get('id') or '')[:12]}` failed "
            f"({failed_dep.get('target', 'unknown')} scope)."
        )
        return msg, CONFIDENCE_LIKELY
    if deploy_state == "failed" and "scope_detected: production" in inventory_evidence:
        return "Latest production deployment failed (inventory evidence).", CONFIDENCE_LIKELY
    if deploy_state == "failed":
        return (
            "Latest deployment failed but production impact is unclear — preview or scope unconfirmed.",
            CONFIDENCE_POSSIBLE,
        )
    if reachability and reachability.get("reachable") is False:
        return "Production URL appears unreachable.", CONFIDENCE_LIKELY
    if reachability and reachability.get("reachable") is True:
        return (
            "No confirmed outage from API evidence; live URL check did not show hard failure.",
            CONFIDENCE_INSUFFICIENT,
        )
    return "Insufficient evidence to determine root cause.", CONFIDENCE_INSUFFICIENT


def enrich_domains_evidence(artifact: ExecutionArtifact, payload: dict[str, Any]) -> None:
    domains = payload.get("domains") or []
    if not domains:
        return
    append_evidence(
        artifact,
        evidence_item(
            source=str(payload.get("source") or "vercel_api"),
            type="domain_inventory",
            confidence=CONFIDENCE_CONFIRMED,
            message=f"Found {len(domains)} domain record(s) via provider API.",
        ),
    )
    for dom in domains[:8]:
        if not isinstance(dom, dict):
            continue
        append_evidence(
            artifact,
            evidence_item(
                source=str(payload.get("source") or "vercel_api"),
                type="domain_record",
                confidence=CONFIDENCE_CONFIRMED,
                message=(
                    f"{dom.get('domain', 'unknown')} · verified={dom.get('verified')} · "
                    f"production={dom.get('production')}"
                ),
                domain=dom.get("domain"),
            ),
        )


def enrich_project_details_evidence(artifact: ExecutionArtifact, payload: dict[str, Any]) -> None:
    details = payload.get("details") or {}
    if not isinstance(details, dict):
        return
    append_evidence(
        artifact,
        evidence_item(
            source=str(payload.get("source") or "vercel_api"),
            type="project_metadata",
            confidence=CONFIDENCE_CONFIRMED,
            message=(
                f"Framework: {details.get('framework') or 'unknown'} · "
                f"repo: {details.get('repo_link') or details.get('repo') or 'unknown'}"
            ),
            framework=details.get("framework"),
            repo=details.get("repo_link") or details.get("repo"),
        ),
    )


def sort_operational_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _key(ev: dict[str, Any]) -> tuple[int, str]:
        at = ev.get("at")
        if at is None:
            return (1, "")
        return (0, str(at))

    return sorted(events, key=_key)
