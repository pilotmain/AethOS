# SPDX-License-Identifier: Apache-2.0
"""Credential requirement guidance — explain missing credentials and setup continuity."""

from __future__ import annotations

import re

from typing import Any

_CREDENTIAL_STATUSES = frozenset({"needs_credential", "needs_credential_repair"})

_PROVIDER_CREDENTIALS: dict[str, dict[str, Any]] = {
    "railway": {
        "env_vars": ["RAILWAY_API_TOKEN"],
        "credential_center_path": "AethOS Credential Center → Providers → Railway",
        "provider_label": "Railway",
    },
    "github": {
        "env_vars": [],
        "credential_center_path": "AethOS Credential Center → Providers → GitHub",
        "provider_label": "GitHub",
    },
    "vercel": {
        "env_vars": [],
        "credential_center_path": "AethOS Credential Center → Providers → Vercel",
        "provider_label": "Vercel",
    },
}


def _provider_config(provider: str) -> dict[str, Any]:
    base = dict(_PROVIDER_CREDENTIALS.get(provider) or {})
    if not base:
        label = provider.replace("_", " ").title()
        base = {
            "env_vars": [],
            "credential_center_path": f"AethOS Credential Center → Providers → {label}",
            "provider_label": label,
        }
    try:
        if provider == "railway":
            from aethos_core.provider_skills.railway.skill import RailwayProviderSkill

            base["env_vars"] = list(RailwayProviderSkill.required_credentials)
    except Exception:
        pass
    return base


def _target_path(preflight: dict[str, Any]) -> str:
    target = preflight.get("target")
    service = preflight.get("target_name")
    project = None
    environment = "production"
    if isinstance(target, dict):
        project = target.get("project_name")
        environment = str(target.get("environment") or environment)
        service = target.get("service_name") or service
    if project and service:
        return f"{project} / {environment} / {service}"
    if service:
        return str(service)
    return "the target"


def _operation_label(operation_type: str) -> str:
    return str(operation_type or "mutation").replace("_", " ")


def _retry_phrase(preflight: dict[str, Any]) -> str:
    request = str(preflight.get("user_request") or "").strip()
    if request:
        return request
    op = _operation_label(str(preflight.get("operation_type") or "mutation"))
    target = preflight.get("target_name")
    if target:
        return f"{op} {target}".strip()
    return op


def detect_missing_credential(preflight: dict[str, Any]) -> dict[str, Any] | None:
    """Return structured missing-credential guidance when preflight is credential-blocked."""
    if not isinstance(preflight, dict):
        return None
    status = str(preflight.get("preflight_status") or "")
    if status not in _CREDENTIAL_STATUSES:
        return None

    provider = str(preflight.get("provider") or "unknown")
    operation_type = str(preflight.get("operation_type") or "mutation")
    config = _provider_config(provider)
    env_vars = list(config.get("env_vars") or [])
    missing = env_vars[:1] if env_vars else [f"{provider.upper()}_API_TOKEN"]
    if status == "needs_credential_repair":
        missing = [f"{config.get('provider_label', provider)} credential (repair required)"]

    provider_label = str(config.get("provider_label") or provider.title())
    target_path = _target_path(preflight)
    op_label = _operation_label(operation_type)

    why_needed = (
        f"Required to submit the {provider_label} {op_label} mutation for {target_path}."
    )
    if status == "needs_credential_repair":
        why_needed = (
            f"Required to decrypt and use the stored {provider_label} credential "
            f"before submitting the {op_label} mutation for {target_path}."
        )

    setup_steps = credential_setup_steps(provider)
    reload_steps = credential_reload_instructions(provider)
    retry_steps = [
        reload_steps[0] if reload_steps else "Restart the AethOS API so credentials are loaded.",
        f"Retry: {_retry_phrase(preflight)}",
        "Approve the new governed preflight.",
    ]

    return {
        "preflight_status": status,
        "provider": provider,
        "provider_label": provider_label,
        "operation_type": operation_type,
        "target_name": preflight.get("target_name"),
        "target_path": target_path,
        "missing_credentials": missing,
        "why_needed": why_needed,
        "setup_steps": setup_steps,
        "reload_instructions": reload_steps,
        "retry_steps": retry_steps,
        "retry_phrase": _retry_phrase(preflight),
        "credential_center_path": str(config.get("credential_center_path") or ""),
        "blocked_reason": (
            "credential_repair_required"
            if status == "needs_credential_repair"
            else "mutation_credentials_missing"
        ),
    }


def credential_setup_steps(provider: str) -> list[dict[str, str]]:
    """Where and how to configure provider credentials."""
    config = _provider_config(provider)
    steps: list[dict[str, str]] = []
    for env_var in config.get("env_vars") or []:
        steps.append(
            {
                "kind": "env",
                "label": f".env: {env_var}=...",
                "detail": f"Add `{env_var}` to your local `.env` file.",
            }
        )
    steps.append(
        {
            "kind": "credential_center",
            "label": str(config.get("credential_center_path") or "AethOS Credential Center"),
            "detail": "Store the provider API token in the encrypted credential vault.",
        }
    )
    steps.append(
        {
            "kind": "verify",
            "label": "Verify provider connection",
            "detail": "Use Credential Center to validate the token before retrying the mutation.",
        }
    )
    return steps


_RAILWAY_TOKEN_CONFIG_RX = re.compile(
    r"\b("
    r"configure\s+(?:the\s+)?(?:railway\s+)?(?:mutation\s+)?(?:api\s+)?token"
    r"|set\s*up\s+(?:the\s+)?railway\s+(?:api\s+)?token"
    r"|add\s+(?:a\s+)?railway\s+(?:api\s+)?token"
    r"|railway\s+(?:mutation\s+)?(?:api\s+)?token\s+(?:setup|configuration)"
    r"|how\s+(?:do\s+i|to)\s+configure\s+(?:the\s+)?railway\s+token"
    r"|RAILWAY_API_TOKEN"
    r")\b",
    re.I,
)


def is_railway_token_configuration_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if "railway" not in raw.lower() and "RAILWAY_API_TOKEN" not in raw:
        return False
    return bool(_RAILWAY_TOKEN_CONFIG_RX.search(raw))


def compose_railway_token_configuration_reply() -> str:
    return "\n".join(
        [
            "To enable **Railway mutation and readiness execution** in AethOS, configure:",
            "",
            "```env",
            "RAILWAY_API_TOKEN=...",
            "```",
            "",
            "**Where to set it:**",
            "- local `.env`",
            "- or **AethOS Credential Center → Providers → Railway**",
            "",
            "Then **restart the AethOS API process** so the token is loaded into this runtime.",
            "",
            "**Verify (from repo root):**",
            "```bash",
            'python -c "from aethos_core.credentials import get_provider_api_token; print(bool(get_provider_api_token(\'railway\')))"',
            "```",
            "",
            "No mutation has been performed.",
        ]
    )


def route_railway_token_configuration_guidance(
    text: str,
) -> tuple[str, str, dict[str, str]] | None:
    if not is_railway_token_configuration_intent(text):
        return None
    return (
        compose_railway_token_configuration_reply(),
        "railway_token_configuration_guidance",
        {
            "route_id": "credential_guidance",
            "matched_module": "credentials.credential_guidance",
            "provider": "railway",
            "credential_key": "RAILWAY_API_TOKEN",
            "readonly": "true",
            "mutation_performed": "false",
            "blocked_handlers": "front_door,generic_capability,devops_capability",
        },
    )


# ──────────────────────────────────────────────────────────────────────────
# Stage 4 — third-party provisioning orchestration (governed plan, no new
# connector files). Each integration maps to a Mission Control vault provider
# and the env var names AethOS would wire into the deployed service. Tokens come
# from the vault only; values are never echoed. A missing token yields a precise
# "needs from you" ask instead of a silent dead end.
# ──────────────────────────────────────────────────────────────────────────

INTEGRATION_PROVISIONING: dict[str, dict[str, Any]] = {
    "stripe": {
        "label": "Stripe",
        "vault_provider": "stripe",
        "env_keys": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
        "category": "payments",
    },
    "supabase": {
        "label": "Supabase",
        "vault_provider": "supabase",
        "env_keys": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"],
        "category": "database",
    },
    "resend": {
        "label": "Resend",
        "vault_provider": "resend",
        "env_keys": ["RESEND_API_KEY"],
        "category": "email",
    },
    "redis": {
        "label": "Redis",
        "vault_provider": "redis",
        "env_keys": ["REDIS_URL"],
        "category": "cache",
    },
}

_INTEGRATION_ALIASES: dict[str, str] = {
    "stripe": "stripe",
    "supabase": "supabase",
    "resend": "resend",
    "redis": "redis",
    "upstash": "redis",
}

_PROVISION_VERB_RX = re.compile(
    r"\b(deploy|provision|set\s*up|setup|connect|wire(?:\s*up)?|spin\s*up|stand\s*up|launch|integrate|add)\b",
    re.I,
)


def detect_requested_integrations(text: str) -> list[str]:
    """Ordered, de-duplicated third-party integrations named in the request."""
    raw = (text or "").lower()
    found: list[str] = []
    for alias, canonical in _INTEGRATION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", raw) and canonical not in found:
            found.append(canonical)
    return found


def _integration_token_present(integration: str) -> bool:
    spec = INTEGRATION_PROVISIONING.get(integration) or {}
    provider = str(spec.get("vault_provider") or integration)
    try:
        from aethos_core.credentials import get_provider_api_token

        if get_provider_api_token(provider, require_validated=False):
            return True
    except Exception:
        pass
    # URL/secret-style integrations (e.g. Redis) may live as a plain env secret.
    import os

    for key in spec.get("env_keys") or []:
        if os.environ.get(key):
            return True
    return False


def assess_integration_provisioning(text: str) -> dict[str, Any]:
    """Resolve which requested integrations are vault-ready vs. need a token."""
    requested = detect_requested_integrations(text)
    integrations: list[dict[str, Any]] = []
    satisfied: list[str] = []
    missing: list[str] = []
    for name in requested:
        spec = INTEGRATION_PROVISIONING[name]
        present = _integration_token_present(name)
        integrations.append(
            {
                "name": name,
                "label": spec["label"],
                "vault_provider": spec["vault_provider"],
                "env_keys": list(spec["env_keys"]),
                "satisfied": present,
            }
        )
        (satisfied if present else missing).append(name)
    return {
        "requested": requested,
        "integrations": integrations,
        "satisfied": satisfied,
        "missing": missing,
    }


def is_provisioning_orchestration_intent(text: str) -> bool:
    """True when the operator asks to deploy/connect ≥1 known third-party."""
    raw = (text or "").strip()
    if not raw:
        return False
    if not detect_requested_integrations(raw):
        return False
    return bool(_PROVISION_VERB_RX.search(raw))


def _provision_target_hint(text: str) -> str:
    raw = (text or "").lower()
    if "vercel" in raw:
        return "Vercel"
    if "railway" in raw:
        return "Railway"
    return "the target service"


def compose_provisioning_orchestration_reply(text: str) -> str:
    """Render a governed, step-by-step provisioning plan with missing-access asks."""
    assessment = assess_integration_provisioning(text)
    integrations = assessment["integrations"]
    target = _provision_target_hint(text)

    lines = [
        f"**Provisioning plan — {target}** (governed, nothing executed yet)",
        "",
        "Each step is approvable in **Mission Control**; AethOS runs the existing "
        "preflight → approval → execute → verify flow per step. Tokens are read "
        "from the Mission Control vault only — never pasted into chat.",
        "",
        "**Planned steps**",
        f"1. Provision / deploy the service on **{target}** (governed deploy preflight).",
        "2. Apply base environment variables to the new service.",
    ]
    step = 3
    for integ in integrations:
        keys = ", ".join(f"`{k}`" for k in integ["env_keys"])
        if integ["satisfied"]:
            state = "vault token present — ready to wire"
        else:
            state = f"**needs from you:** a **{integ['label']}** token in the vault"
        lines.append(f"{step}. Connect **{integ['label']}** → set {keys} ({state}).")
        step += 1
    lines.append(f"{step}. Verify health (reachable service + post-mutation checks).")

    if assessment["missing"]:
        lines.extend(["", "**Needs from you before those steps can run:**"])
        for name in assessment["missing"]:
            spec = INTEGRATION_PROVISIONING[name]
            lines.append(
                f"- **{spec['label']}** API token — add it in "
                f"**Mission Control → Advanced settings → Credentials → {spec['label']}**. "
                f"AethOS will then wire {', '.join(spec['env_keys'])}."
            )
        lines.append("")
        lines.append(
            "I can proceed with the steps that are ready now and pause on the rest, "
            "or wait until every token is in the vault — your call."
        )
    else:
        if integrations:
            lines.extend(
                [
                    "",
                    "All requested integrations have a vault token. Approve the plan in "
                    "Mission Control and I'll execute each governed step in order.",
                ]
            )

    lines.extend(["", "**No mutation has been performed yet.**"])
    return "\n".join(lines)


def route_provisioning_orchestration(
    text: str,
    *,
    session_id: str | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    """Governed provisioning orchestration plan for deploy + third-party connect."""
    _ = session_id
    try:
        from aethos_core.config import get_settings

        if not getattr(get_settings(), "provisioning_orchestration_enabled", False):
            return None
    except Exception:
        return None
    if not is_provisioning_orchestration_intent(text):
        return None
    assessment = assess_integration_provisioning(text)
    return (
        compose_provisioning_orchestration_reply(text),
        "provisioning_orchestration_plan",
        {
            "route_id": "provisioning_orchestration",
            "matched_module": "credentials.credential_guidance",
            "lane": "provisioning_orchestration",
            "integrations": ",".join(assessment["requested"]),
            "missing_credentials": ",".join(assessment["missing"]),
            "readonly": "true",
            "mutation_performed": "false",
            "governed": "true",
        },
    )


def credential_reload_instructions(provider: str) -> list[str]:
    """Steps to reload credentials into the running AethOS runtime."""
    _ = provider
    return [
        "Restart the AethOS API so the credential is loaded.",
        "Or use Mission Control → Refresh credentials to reload the credential vault without a full restart when supported.",
    ]


def compose_missing_credential_reply(preflight: dict[str, Any]) -> str | None:
    """Operator-facing explanation for a credential-blocked preflight."""
    guidance = detect_missing_credential(preflight)
    if not guidance:
        return None

    provider_label = guidance["provider_label"]
    status = guidance["preflight_status"]
    if status == "needs_credential_repair":
        opener = (
            f"This mutation cannot be approved yet because the stored **{provider_label}** "
            "credential must be repaired before AethOS can submit provider mutations."
        )
    else:
        opener = (
            f"This mutation cannot be approved yet because AethOS does not have "
            f"**{provider_label}** mutation credentials configured."
        )

    lines = [
        opener,
        "",
        "**Missing credential:**",
    ]
    for cred in guidance["missing_credentials"]:
        lines.append(f"- `{cred}`")

    lines.extend(
        [
            "",
            "**Why needed:**",
            f"- {guidance['why_needed']}",
            "",
            "**Where to configure:**",
        ]
    )
    for step in guidance["setup_steps"]:
        if step["kind"] == "env":
            lines.append(f"- {step['label']}")
        elif step["kind"] == "credential_center":
            lines.append(f"- or {step['label']}")

    lines.extend(["", "**After adding it:**"])
    for idx, step in enumerate(guidance["retry_steps"], start=1):
        lines.append(f"{idx}. {step}")

    lines.append("")
    lines.append("**No mutation has been performed yet.**")
    return "\n".join(lines)


def _preflight_dict_from_job(job: Any) -> dict[str, Any]:
    params = dict(getattr(job, "params", None) or {})
    pf = dict(params.get("mutation_preflight") or {})
    merged = {**pf, **params}
    merged.setdefault("preflight_status", pf.get("preflight_status") or params.get("preflight_status"))
    merged.setdefault("provider", pf.get("provider") or params.get("provider"))
    merged.setdefault("operation_type", pf.get("operation_type") or params.get("operation_type"))
    merged.setdefault("target_name", pf.get("target_name") or params.get("target_name"))
    merged.setdefault("target", pf.get("target") or params.get("target"))
    merged.setdefault("user_request", params.get("user_request") or pf.get("user_request"))
    if params.get("credential_guidance"):
        merged["credential_guidance"] = params["credential_guidance"]
    return merged


def build_credential_requirements_for_job(job_id: str) -> dict[str, Any] | None:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return None
    preflight = _preflight_dict_from_job(job)
    guidance = preflight.get("credential_guidance") or detect_missing_credential(preflight)
    if not guidance:
        return None
    return {
        "ok": True,
        "job_id": job_id,
        "preflight_status": guidance.get("preflight_status"),
        "provider": guidance.get("provider"),
        "guidance": guidance,
        "reply": compose_missing_credential_reply(preflight),
        "mutation_approvable": False,
    }


def find_latest_credential_blocked_preflight(
    *,
    session_id: str | None = None,
) -> tuple[str, dict[str, Any]] | None:
    from aethos_core.runtime.job_types import uses_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for job in job_store.list_all():
        if session_id and str(getattr(job, "session_id", "") or "") != session_id:
            continue
        if not uses_mutation_preflight(job.job_type):
            continue
        params = dict(job.params or {})
        if params.get("is_current") is False:
            continue
        preflight = _preflight_dict_from_job(job)
        status = str(preflight.get("preflight_status") or "")
        if status not in _CREDENTIAL_STATUSES:
            continue
        updated = float(getattr(job, "updated_at", 0) or getattr(job, "created_at", 0) or 0)
        candidates.append((updated, job.id, preflight))

    if not candidates:
        return None
    candidates.sort(key=lambda row: row[0], reverse=True)
    _, job_id, preflight = candidates[0]
    return job_id, preflight


def attach_credential_guidance_to_preflight(outcome_dict: dict[str, Any]) -> dict[str, Any]:
    guidance = detect_missing_credential(outcome_dict)
    if guidance:
        outcome_dict["credential_guidance"] = guidance
        outcome_dict["credential_requirements_reply"] = compose_missing_credential_reply(outcome_dict)
    return outcome_dict


def rerun_mutation_preflight_for_job(job_id: str) -> dict[str, Any]:
    """Re-run mutation preflight after credentials change."""
    from aethos_core.jobs.job_approval_guidance import build_mutation_approval_metadata
    from aethos_core.operations.mutations.preflight import run_mutation_preflight
    from aethos_core.runtime.job_types import uses_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job or not uses_mutation_preflight(job.job_type):
        return {"ok": False, "reason": "job_not_found_or_not_mutation_preflight", "job_id": job_id}

    outcome = run_mutation_preflight(job_type=job.job_type, params=dict(job.params or {}))
    outcome_dict = attach_credential_guidance_to_preflight(outcome.to_dict())
    job = job_store.get(job_id)
    if job:
        job.params["mutation_preflight"] = outcome_dict
        job.params["preflight_status"] = outcome.preflight_status
        job.params["execution_blocked"] = outcome.preflight_status != "ready_for_mutation_approval"
        job.params["credential_guidance"] = outcome_dict.get("credential_guidance")
        job.params["credential_requirements_reply"] = outcome_dict.get("credential_requirements_reply")
        job.params.update(build_mutation_approval_metadata(preflight_status=outcome.preflight_status))
        job.result_summary = outcome.summary
        job.result = outcome.full_result

    return {
        "ok": True,
        "job_id": job_id,
        "preflight_status": outcome.preflight_status,
        "mutation_approvable": outcome.preflight_status == "ready_for_mutation_approval",
        "credential_guidance": outcome_dict.get("credential_guidance"),
        "requirements": build_credential_requirements_for_job(job_id),
    }
