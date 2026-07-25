# SPDX-License-Identifier: Apache-2.0
"""FIX 354 / WORKSTREAM_G1 — real evidence density & trust maturity executor."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_contract import (
    EVIDENCE_DOMAINS,
    STALE_EVIDENCE_DAYS,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store import (
    list_evidence_domain_registry_entries,
    register_evidence_domain_entry,
)

_EVIDENCE_SOURCE_CATALOG: tuple[tuple[str, str, str, str], ...] = (
    (
        "f1_customer_delivery",
        "aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store",
        "list_first_customer_delivery_pilot_records",
        "customer",
    ),
    (
        "f1_pilot_runs",
        "aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store",
        "list_customer_pilot_run_registry_entries",
        "delivery",
    ),
    (
        "f2_customer_value",
        "aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store",
        "list_customer_value_adoption_validation_records",
        "customer",
    ),
    (
        "f2_usage_observations",
        "aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store",
        "list_usage_observation_registry_entries",
        "customer",
    ),
    (
        "f3_multi_customer",
        "aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store",
        "list_multi_customer_value_proof_records",
        "customer",
    ),
    (
        "f4_scale_validation",
        "aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store",
        "list_customer_scale_validation_records",
        "operational",
    ),
    (
        "f5_commercial_validation",
        "aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store",
        "list_commercial_validation_records",
        "customer",
    ),
    (
        "f6_unit_economics",
        "aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store",
        "list_business_sustainability_records",
        "operational",
    ),
    (
        "f7_operating_model",
        "aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store",
        "list_operating_model_records",
        "operational",
    ),
    (
        "et_workspace",
        "aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store",
        "list_governed_workspace_creation_records",
        "delivery",
    ),
    (
        "et_generation",
        "aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store",
        "list_governed_code_generation_records",
        "delivery",
    ),
    (
        "et_git_delivery",
        "aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store",
        "list_governed_git_delivery_records",
        "delivery",
    ),
    (
        "et_deployment",
        "aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store",
        "list_governed_deployment_execution_records",
        "provider",
    ),
    (
        "et_certification",
        "aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store",
        "list_governed_end_to_end_delivery_certification_records",
        "delivery",
    ),
    (
        "d2_multi_cloud_proof",
        "aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_store",
        "list_multi_cloud_operational_proof_records",
        "provider",
    ),
    (
        "real_world_delivery_proof",
        "aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store",
        "list_real_world_delivery_proof_records",
        "delivery",
    ),
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _classify_record(record: dict[str, Any], *, source_id: str, domain: str) -> str:
    kind = str(record.get("kind") or "").lower()
    content = str(record.get("content") or "").lower()

    if record.get("placeholder") is True or "placeholder" in kind or "placeholder" in content:
        return "synthetic"
    if kind.endswith("_review_approve") or "human approves" in content:
        return "independent"
    if record.get("passed") is not None or record.get("stage_results") or source_id.startswith("et_"):
        return "operational"
    if record.get("run_id") or record.get("deployment_id") or "pilot_run" in kind:
        return "operational"
    if record.get("observation_id") or "usage_observation" in kind:
        return "operational"
    if record.get("composed_read_only") is True or "composed" in content:
        return "derived"
    if "report" in kind or "dashboard" in kind or "metrics" in kind:
        return "derived"
    if domain == "trust" and "review" in kind:
        return "independent"
    if not record and source_id:
        return "synthetic"
    return "derived"


def _load_source_rows(source_id: str, module_path: str, list_fn: str) -> list[dict[str, Any]]:
    try:
        mod = __import__(module_path, fromlist=[list_fn])
        rows = getattr(mod, list_fn)()
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []
    return []


def _collect_evidence_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source_id, module_path, list_fn, domain in _EVIDENCE_SOURCE_CATALOG:
        rows = _load_source_rows(source_id, module_path, list_fn)
        for row in rows:
            classification = _classify_record(row, source_id=source_id, domain=domain)
            timestamp = (
                _parse_timestamp(row.get("recorded_at"))
                or _parse_timestamp(row.get("registered_at"))
                or _parse_timestamp(row.get("created_at"))
            )
            items.append(
                {
                    "source_id": source_id,
                    "domain": domain,
                    "classification": classification,
                    "kind": row.get("kind"),
                    "record_id": row.get("record_id") or row.get("run_id") or row.get("observation_id"),
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "session_id": row.get("session_id") or row.get("program_session_id"),
                }
            )
    return items


def build_evidence_registry_inventory(*, program_session_id: str) -> dict[str, Any]:
    domain_entries = [
        row
        for row in list_evidence_domain_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]
    sources: list[dict[str, Any]] = []
    for source_id, module_path, list_fn, domain in _EVIDENCE_SOURCE_CATALOG:
        rows = _load_source_rows(source_id, module_path, list_fn)
        sources.append(
            {
                "source_id": source_id,
                "module_path": module_path,
                "list_function": list_fn,
                "domain": domain,
                "record_count": len(rows),
                "store_populated": len(rows) > 0,
            }
        )

    return {
        "inventory_id": "evidence-registry-inventory",
        "program_session_id": program_session_id,
        "fix_evidence_stores": [s for s in sources if s["domain"] in {"customer", "operational", "fix_evidence"}],
        "execution_receipts": [s for s in sources if s["source_id"].startswith("et_")],
        "trust_freeze_and_review_sources": [
            s for s in sources if s["domain"] in {"trust", "customer", "operational"}
        ],
        "audit_records": [s for s in sources if "audit" in s["source_id"] or s["domain"] == "audit"],
        "customer_records": [s for s in sources if s["domain"] == "customer"],
        "provider_records": [s for s in sources if s["domain"] == "provider"],
        "registered_domains": domain_entries,
        "sources": sources,
        "source_count": len(sources),
        "read_only": True,
    }


def build_evidence_density_report(*, program_session_id: str) -> dict[str, Any]:
    items = _collect_evidence_items()
    counts = {"real": 0, "synthetic": 0, "derived": 0, "operational": 0, "independent": 0}
    for item in items:
        classification = str(item.get("classification") or "derived")
        counts[classification] = counts.get(classification, 0) + 1
        if classification in {"operational", "independent"}:
            counts["real"] += 1

    total = len(items) or 1
    density = round(counts["real"] / total, 3)

    return {
        "report_id": "evidence-density-report",
        "program_session_id": program_session_id,
        "total_evidence_items": len(items),
        "real_evidence_count": counts["real"],
        "derived_evidence_count": counts["derived"],
        "synthetic_evidence_count": counts["synthetic"],
        "operational_evidence_count": counts["operational"],
        "independent_evidence_count": counts["independent"],
        "placeholder_evidence_count": counts["synthetic"],
        "evidence_density_score": density,
        "trust_promotion_performed": False,
        "read_only": True,
    }


def build_evidence_freshness_report(*, program_session_id: str) -> dict[str, Any]:
    items = _collect_evidence_items()
    now = datetime.now(timezone.utc)
    active = 0
    stale = 0
    missing_timestamp = 0
    ages: list[int] = []

    for item in items:
        ts = _parse_timestamp(item.get("timestamp"))
        if ts is None:
            missing_timestamp += 1
            continue
        age_days = max(0, (now - ts).days)
        ages.append(age_days)
        if age_days <= STALE_EVIDENCE_DAYS:
            active += 1
        else:
            stale += 1

    avg_age = round(sum(ages) / len(ages), 1) if ages else 0.0
    freshness = round(active / max(len(items), 1), 3)

    return {
        "report_id": "evidence-freshness-report",
        "program_session_id": program_session_id,
        "active_evidence_count": active,
        "stale_evidence_count": stale,
        "missing_refresh_timestamp_count": missing_timestamp,
        "average_evidence_age_days": avg_age,
        "stale_threshold_days": STALE_EVIDENCE_DAYS,
        "evidence_freshness_score": freshness,
        "read_only": True,
    }


def build_evidence_provenance_report(*, program_session_id: str) -> dict[str, Any]:
    items = _collect_evidence_items()
    by_domain: dict[str, dict[str, int]] = {domain: {"total": 0, "operational": 0, "independent": 0} for domain in EVIDENCE_DOMAINS}

    for item in items:
        domain = str(item.get("domain") or "operational")
        if domain not in by_domain:
            by_domain[domain] = {"total": 0, "operational": 0, "independent": 0}
        by_domain[domain]["total"] += 1
        classification = str(item.get("classification") or "")
        if classification == "operational":
            by_domain[domain]["operational"] += 1
        if classification == "independent":
            by_domain[domain]["independent"] += 1

    return {
        "report_id": "evidence-provenance-report",
        "program_session_id": program_session_id,
        "customer_evidence": by_domain.get("customer", {}),
        "delivery_evidence": by_domain.get("delivery", {}),
        "provider_evidence": by_domain.get("provider", {}),
        "operational_evidence": by_domain.get("operational", {}),
        "trust_evidence": by_domain.get("trust", {}),
        "audit_evidence": by_domain.get("audit", {}),
        "fix_evidence": by_domain.get("fix_evidence", {}),
        "provenance_by_domain": by_domain,
        "read_only": True,
    }


def build_trust_maturity_report(*, program_session_id: str) -> dict[str, Any]:
    items = _collect_evidence_items()
    review_kinds = [i for i in items if "review" in str(i.get("kind") or "")]
    independent = [i for i in items if i.get("classification") == "independent"]
    operational = [i for i in items if i.get("classification") == "operational"]

    trust_decisions = len(independent)
    operational_proof = len(operational)
    total = len(items) or 1

    return {
        "report_id": "trust-maturity-report",
        "program_session_id": program_session_id,
        "trust_freeze_coverage": round(len(review_kinds) / total, 3),
        "trust_decision_coverage": round(trust_decisions / total, 3),
        "operational_proof_coverage": round(operational_proof / total, 3),
        "independent_validation_coverage": round(len(independent) / total, 3),
        "trust_maturity_score": round((trust_decisions + operational_proof) / max(total, 1), 3),
        "trust_authority_granted": False,
        "read_only": True,
    }


def build_evidence_gap_registry(*, program_session_id: str) -> dict[str, Any]:
    inventory = build_evidence_registry_inventory(program_session_id=program_session_id)
    density = build_evidence_density_report(program_session_id=program_session_id)
    freshness = build_evidence_freshness_report(program_session_id=program_session_id)
    provenance = build_evidence_provenance_report(program_session_id=program_session_id)
    gaps: list[dict[str, Any]] = []

    for source in inventory.get("sources") or []:
        if not source.get("store_populated"):
            gaps.append(
                {
                    "gap_id": f"empty-store-{source.get('source_id')}",
                    "category": "missing_evidence",
                    "detail": f"No records in {source.get('source_id')}",
                }
            )

    if float(density.get("synthetic_evidence_count") or 0) > float(density.get("real_evidence_count") or 0):
        gaps.append(
            {
                "gap_id": "synthetic-dominance",
                "category": "sparse_evidence",
                "detail": "Synthetic or placeholder evidence exceeds real evidence volume",
            }
        )

    if int(freshness.get("stale_evidence_count") or 0) > 0:
        gaps.append(
            {
                "gap_id": "stale-evidence",
                "category": "weak_evidence",
                "detail": "Stale evidence exceeds active evidence threshold",
            }
        )

    for domain, stats in (provenance.get("provenance_by_domain") or {}).items():
        if stats.get("total", 0) == 0:
            gaps.append(
                {
                    "gap_id": f"missing-domain-{domain}",
                    "category": "unsupported_assumption",
                    "detail": f"No evidence collected for domain {domain}",
                }
            )

    return {
        "registry_id": "evidence-gap-registry",
        "program_session_id": program_session_id,
        "gap_count": len(gaps),
        "missing_evidence": [g for g in gaps if g.get("category") == "missing_evidence"],
        "sparse_evidence": [g for g in gaps if g.get("category") == "sparse_evidence"],
        "weak_evidence": [g for g in gaps if g.get("category") == "weak_evidence"],
        "unsupported_assumptions": [g for g in gaps if g.get("category") == "unsupported_assumption"],
        "gaps": gaps[:30],
        "read_only": True,
    }


def build_evidence_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    gaps = build_evidence_gap_registry(program_session_id=program_session_id)
    collection: list[dict[str, Any]] = []
    operational: list[dict[str, Any]] = []
    customer: list[dict[str, Any]] = []
    provider: list[dict[str, Any]] = []

    for gap in gaps.get("gaps") or []:
        category = str(gap.get("category") or "")
        opportunity = {
            "gap_id": gap.get("gap_id"),
            "opportunity": f"Collect evidence to close {gap.get('detail')}",
            "advisory_only": True,
            "automatic_evidence_acceptance": False,
        }
        collection.append(opportunity)
        if "store" in str(gap.get("detail") or "").lower() and "et_" in str(gap.get("gap_id") or ""):
            operational.append(opportunity)
        elif "customer" in str(gap.get("gap_id") or ""):
            customer.append(opportunity)
        elif "provider" in str(gap.get("gap_id") or ""):
            provider.append(opportunity)
        elif category == "missing_evidence":
            operational.append(opportunity)

    opportunities = collection
    return {
        "registry_id": "evidence-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "evidence_collection_opportunities": collection[:15],
        "operational_proof_opportunities": operational[:10],
        "customer_validation_opportunities": customer[:10],
        "provider_validation_opportunities": provider[:10],
        "read_only": True,
    }


def compute_evidence_maturity_metrics(*, program_session_id: str) -> dict[str, Any]:
    density = build_evidence_density_report(program_session_id=program_session_id)
    freshness = build_evidence_freshness_report(program_session_id=program_session_id)
    trust = build_trust_maturity_report(program_session_id=program_session_id)
    provenance = build_evidence_provenance_report(program_session_id=program_session_id)

    customer_total = int((provenance.get("customer_evidence") or {}).get("total") or 0)
    provider_total = int((provenance.get("provider_evidence") or {}).get("total") or 0)
    audit_total = int((provenance.get("audit_evidence") or {}).get("total") or 0)
    inventory = build_evidence_registry_inventory(program_session_id=program_session_id)
    populated_sources = sum(1 for s in inventory.get("sources") or [] if s.get("store_populated"))
    source_count = len(inventory.get("sources") or []) or 1

    return {
        "evidence_density_score": density.get("evidence_density_score", 0.0),
        "evidence_freshness_score": freshness.get("evidence_freshness_score", 0.0),
        "trust_maturity_score": trust.get("trust_maturity_score", 0.0),
        "operational_proof_coverage": trust.get("operational_proof_coverage", 0.0),
        "customer_evidence_coverage": round(customer_total / max(populated_sources, 1), 3),
        "provider_evidence_coverage": round(provider_total / max(source_count, 1), 3),
        "audit_evidence_coverage": round(audit_total / max(source_count, 1), 3),
        "read_only": True,
    }


def register_evidence_domain_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    domain = kv.get("domain") or kv.get("domain_id") or "operational"
    entry = register_evidence_domain_entry(
        entry={
            "domain_id": domain,
            "program_session_id": program_session_id,
            "source": kv.get("source") or kv.get("source_id") or "platform",
            "focus": kv.get("focus") or "evidence_density",
        }
    )
    from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store import (
        append_evidence_maturity_record,
    )

    append_evidence_maturity_record(
        session_id=program_session_id,
        kind="evidence_domain_entry",
        content=body,
        metadata=entry,
    )
    return entry
