# SPDX-License-Identifier: Apache-2.0
"""Handle user-provided repository binding corrections."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.provider_topology.binding_update_flow import (
    PendingBindingCorrection,
    apply_binding_update,
    confirm_pending_update,
    get_pending_correction,
    store_pending_correction,
)
from aethos_core.provider_topology.github_access_verifier import verify_github_repo_access
from aethos_core.provider_topology.repo_reference_parser import (
    RepoReference,
    is_railway_restart_with_repo_target,
    parse_repo_reference,
    repo_matches_service_name,
)
from aethos_core.provider_topology.topology_memory import get_binding

_CONFIRM_RX = re.compile(
    r"\b("
    r"yes\s+update(?:\s+it)?"
    r"|update\s+the\s+binding"
    r"|use\s+that\s+repo"
    r"|yes\s+use\s+[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*"
    r"|confirm"
    r")\b",
    re.I,
)
_CORRECTION_CUE_RX = re.compile(r"\b(?:instead|use\s+this|correct\s+repo|right\s+repo)\b", re.I)
_TRANSFER_CUE_RX = re.compile(
    r"\b("
    r"repo\s+(?:moved|transferred|renamed)"
    r"|repository\s+(?:moved|transferred|renamed)"
    r"|reconcile(?:\s+(?:source|repo|binding(?:\s+binding)?)?)?"
    r"|check(?:\s+the)?\s+(?:git\s+)?remote"
    r"|refresh(?:\s+the)?\s+(?:source|repo)\s+binding"
    r")\b",
    re.I,
)


def is_binding_confirmation(text: str) -> bool:
    return bool(_CONFIRM_RX.search(text or ""))


def _active_thread(session_id: str):
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired

    thread = get_active_thread(session_id=session_id)
    if thread is None or is_thread_expired(thread):
        return None
    if thread.status in {"completed", "cancelled", "superseded"}:
        return None
    return thread


def _thread_has_source_binding_failure(thread) -> bool:
    failure = thread.failure_reason or {}
    if failure.get("failure_stage") == "source_binding":
        return True
    reason = str(failure.get("failure_reason") or "").lower()
    return "github installation" in reason or "installation found for repo" in reason or "source binding" in reason


def should_handle_binding_correction(text: str, *, session_id: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if is_binding_confirmation(raw):
        return get_pending_correction(session_id=session_id) is not None
    if _TRANSFER_CUE_RX.search(raw):
        return True
    repo_ref = parse_repo_reference(raw)
    if repo_ref is None:
        return False
    thread = _active_thread(session_id)
    if thread is not None and _thread_has_source_binding_failure(thread):
        return True
    if thread is not None and repo_matches_service_name(repo_ref, str(thread.service or "")):
        return True
    if is_railway_restart_with_repo_target(raw):
        return True
    if _CORRECTION_CUE_RX.search(raw):
        return True
    if get_pending_correction(session_id=session_id) is not None:
        return True
    return False


def _auto_update_allowed(*, thread, old_repo: str | None, new_repo: str, access_ok: bool, user_text: str) -> bool:
    if thread is None or not access_ok:
        return False
    if not _thread_has_source_binding_failure(thread):
        return False
    if not repo_matches_service_name(RepoReference.from_dict({"full_name": new_repo}), str(thread.service or "")):
        return False
    if old_repo and old_repo.lower() == new_repo.lower():
        return False
    if not _CORRECTION_CUE_RX.search(user_text or ""):
        return False
    old_access = verify_github_repo_access(old_repo) if old_repo else None
    if old_access and old_access.ok:
        return False
    return True


def process_binding_correction(
    text: str,
    *,
    session_id: str = "default",
    accessible_repos: list[str] | None = None,
) -> dict[str, Any]:
    raw = (text or "").strip()

    if is_binding_confirmation(raw):
        outcome = confirm_pending_update(session_id=session_id)
        if not outcome.get("ok"):
            return {"kind": "confirm_failed", "message": str(outcome.get("error") or "Confirmation failed."), "outcome": outcome}
        from aethos_core.provider_topology.retry_offer import offer_retry_after_binding_update

        offer_retry_after_binding_update(
            session_id=session_id,
            provider=str(outcome.get("binding", {}).get("provider") or "railway"),
            project=str(outcome.get("binding", {}).get("project") or ""),
            environment=str(outcome.get("binding", {}).get("environment") or "production"),
            service=str(outcome.get("binding", {}).get("service_name") or ""),
            operation="restart",
            source_binding=str(outcome.get("new_repo") or ""),
        )
        return {
            "kind": "binding_updated",
            "message": (
                f"Updated the source binding:\n**{outcome.get('service_path')}**\n→ **{outcome.get('new_repo')}**\n\n"
                "I can now create a new governed restart preflight using the corrected binding."
            ),
            "outcome": outcome,
        }

    if _TRANSFER_CUE_RX.search(raw):
        return process_repo_transfer_reconciliation(session_id=session_id, accessible_repos=accessible_repos)

    repo_ref = parse_repo_reference(raw)
    if repo_ref is None:
        return {"kind": "no_repo", "message": "No GitHub repository reference found."}

    thread = _active_thread(session_id)
    binding = None
    if thread is not None:
        binding = get_binding(
            provider=thread.provider,
            project=str(thread.project or ""),
            environment=str(thread.environment or "production"),
            service_name=str(thread.service or ""),
        )
    elif is_railway_restart_with_repo_target(raw):
        from aethos_core.provider_topology.topology_memory import find_binding_by_service_name

        binding = find_binding_by_service_name(repo_ref.repo)

    if thread is None and binding is None:
        return {
            "kind": "no_thread",
            "message": (
                f"I found repository **{repo_ref.full_name}**, but no active Railway thread is bound.\n\n"
                "Tell me which Railway service this repo should bind to, or start a governed restart first."
            ),
            "repo_ref": repo_ref.to_dict(),
        }

    provider = thread.provider if thread else (binding.provider if binding else "railway")
    project = str(thread.project if thread else (binding.project if binding else ""))
    environment = str(thread.environment if thread else (binding.environment if binding else "production"))
    service_name = str(thread.service if thread else (binding.service_name if binding else repo_ref.repo))
    old_repo = binding.github_repo if binding else None

    access = verify_github_repo_access(repo_ref.full_name, accessible_repos=accessible_repos)
    auto_allowed = _auto_update_allowed(
        thread=thread,
        old_repo=old_repo,
        new_repo=repo_ref.full_name,
        access_ok=access.ok,
        user_text=raw,
    )

    pending = PendingBindingCorrection(
        session_id=session_id,
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        old_repo=old_repo,
        new_repo=repo_ref.full_name,
        access_verified=access.ok,
        auto_update_allowed=auto_allowed,
    )
    store_pending_correction(pending)

    if auto_allowed:
        outcome = apply_binding_update(
            provider=provider,
            project=project,
            environment=environment,
            service_name=service_name,
            github_repo=repo_ref.full_name,
            service_id=binding.service_id if binding else None,
        )
        from aethos_core.provider_topology.binding_update_flow import clear_pending_correction

        clear_pending_correction(session_id=session_id)
        from aethos_core.provider_topology.retry_offer import offer_retry_after_binding_update

        offer_retry_after_binding_update(
            session_id=session_id,
            provider=provider,
            project=project,
            environment=environment,
            service=service_name,
            operation=str(thread.operation if thread else "restart") or "restart",
            source_binding=repo_ref.full_name,
        )
        return {
            "kind": "binding_updated",
            "message": (
                "Got it — I found a corrected source binding for the active Railway service.\n\n"
                f"Current Railway service:\n- **{pending.service_path()}**\n\n"
                f"Old stored repo:\n- **{old_repo or '(none)'}**\n\n"
                f"New candidate repo:\n- **{repo_ref.full_name}**\n\n"
                f"I verified GitHub access for **{repo_ref.full_name}**.\n\n"
                f"I updated the source binding for **{pending.service_path()}**.\n\n"
                "I can now create a new governed Railway restart preflight using the corrected binding."
            ),
            "outcome": outcome,
            "repo_ref": repo_ref.to_dict(),
        }

    if not access.ok:
        from aethos_core.provider_topology.repo_reconciliation import reconcile_source_binding

        reconciliation = reconcile_source_binding(
            provider=provider,
            project=project,
            environment=environment,
            service_name=service_name,
            old_repo=old_repo or "",
            candidate_repo=repo_ref.full_name,
            accessible_repos=accessible_repos,
        )
        extra = ""
        if reconciliation.railway_metadata and reconciliation.railway_metadata.stale:
            extra = (
                f"\n\nRailway note: the service still appears linked to **{reconciliation.railway_metadata.linked_repo}**. "
                f"Update Railway source connection to **{repo_ref.full_name}** or reconnect the GitHub app."
            )
        return {
            "kind": "access_failed",
            "message": (
                "Got it — I found a corrected source binding for the active Railway service.\n\n"
                f"Current Railway service:\n- **{pending.service_path()}**\n\n"
                f"Old stored repo:\n- **{old_repo or '(none)'}**\n\n"
                f"New candidate repo:\n- **{repo_ref.full_name}**\n\n"
                f"I still cannot verify GitHub installation access for **{repo_ref.full_name}**.\n\n"
                "No binding was changed and no restart was attempted."
                f"{extra}"
            ),
            "repo_ref": repo_ref.to_dict(),
            "access": access.to_dict(),
            "reconciliation": reconciliation.to_dict(),
        }

    return {
        "kind": "confirmation_needed",
        "message": (
            "Got it — I found a corrected source binding for the active Railway service.\n\n"
            f"Current Railway service:\n- **{pending.service_path()}**\n\n"
            f"Old stored repo:\n- **{old_repo or '(none)'}**\n\n"
            f"New candidate repo:\n- **{repo_ref.full_name}**\n\n"
            f"I verified GitHub access for **{repo_ref.full_name}**.\n\n"
            f"Should I update the source binding for **{service_name}** to **{repo_ref.full_name}** before retrying the restart?\n\n"
            "Reply **yes update it** to apply the binding change."
        ),
        "repo_ref": repo_ref.to_dict(),
        "pending": pending.to_dict(),
    }


def process_restart_with_repo_target(
    text: str,
    *,
    session_id: str = "default",
    accessible_repos: list[str] | None = None,
) -> dict[str, Any] | None:
    if not is_railway_restart_with_repo_target(text):
        return None
    repo_ref = parse_repo_reference(text)
    if repo_ref is None:
        return None
    thread = _active_thread(session_id)
    from aethos_core.provider_topology.topology_memory import find_binding_by_service_name

    binding = None
    if thread is not None:
        binding = get_binding(
            provider=thread.provider,
            project=str(thread.project or ""),
            environment=str(thread.environment or "production"),
            service_name=str(thread.service or ""),
        )
    else:
        binding = find_binding_by_service_name(repo_ref.repo)
    old_repo = binding.github_repo if binding else None
    service_path = (
        f"{thread.project} / {thread.environment} / {thread.service}"
        if thread
        else (binding.service_path() if binding else f"unknown / production / {repo_ref.repo}")
    )
    access = verify_github_repo_access(repo_ref.full_name, accessible_repos=accessible_repos)
    if thread is not None or binding is not None:
        store_pending_correction(
            PendingBindingCorrection(
                session_id=session_id,
                provider="railway",
                project=str(thread.project if thread else (binding.project if binding else "")),
                environment=str(thread.environment if thread else (binding.environment if binding else "production")),
                service_name=str(thread.service if thread else (binding.service_name if binding else repo_ref.repo)),
                old_repo=old_repo,
                new_repo=repo_ref.full_name,
                access_verified=access.ok,
            )
        )
    return {
        "kind": "restart_repo_not_service",
        "message": (
            f"I recognize **{repo_ref.full_name}** as a GitHub repository, not a Railway service.\n\n"
            f"For the active Railway service:\n- **{service_path}**\n\n"
            f"Should I update the source binding from **{old_repo or '(none)'}** to **{repo_ref.full_name}** before retrying the restart?\n\n"
            "Reply **yes update it** to apply the binding change."
        ),
        "repo_ref": repo_ref.to_dict(),
    }


def process_repo_transfer_reconciliation(
    *,
    session_id: str = "default",
    accessible_repos: list[str] | None = None,
    local_path: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    from aethos_core.provider_topology.repo_reconciliation import (
        compose_reconciliation_reply,
        refresh_binding_from_remote,
        reconcile_source_binding,
        suggest_repo_from_transfer,
    )

    thread = _active_thread(session_id)
    if thread is None:
        return {
            "kind": "no_thread",
            "message": "No active operational thread to reconcile repository transfer against.",
        }

    binding = get_binding(
        provider=thread.provider,
        project=str(thread.project or ""),
        environment=str(thread.environment or "production"),
        service_name=str(thread.service or ""),
    )
    old_repo = str(binding.github_repo if binding and binding.github_repo else "")
    if not old_repo and thread.failure_reason:
        reason = str((thread.failure_reason or {}).get("failure_reason") or "")
        import re

        match = re.search(r"repo:\s*([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)", reason, re.I)
        if match:
            old_repo = match.group(1)

    suggested = suggest_repo_from_transfer(old_repo, accessible_repos=accessible_repos) if old_repo else None
    if confirm and suggested:
        result = refresh_binding_from_remote(
            provider=thread.provider,
            project=str(thread.project or ""),
            environment=str(thread.environment or "production"),
            service_name=str(thread.service or ""),
            local_path=local_path,
            confirm=True,
            accessible_repos=accessible_repos,
        )
    else:
        result = reconcile_source_binding(
            provider=thread.provider,
            project=str(thread.project or ""),
            environment=str(thread.environment or "production"),
            service_name=str(thread.service or ""),
            old_repo=old_repo,
            candidate_repo=suggested,
            local_path=local_path,
            session_id=session_id,
            accessible_repos=accessible_repos,
        )

    message = compose_reconciliation_reply(result)
    if result.can_auto_update and result.confirmed_repo and not result.updated:
        message += f"\n\nReply **yes update it** to apply **{result.confirmed_repo}** to the canonical AethOS binding."
    elif result.updated:
        from aethos_core.provider_topology.retry_offer import offer_retry_after_binding_update

        offer_retry_after_binding_update(
            session_id=session_id,
            provider=thread.provider,
            project=str(thread.project or ""),
            environment=str(thread.environment or "production"),
            service=str(thread.service or ""),
            operation=str(thread.operation or "restart"),
            source_binding=str(result.confirmed_repo or ""),
        )
        message += "\n\nI can now create a new governed restart preflight using the reconciled binding."

    kind = "binding_updated" if result.updated else "repo_reconciliation"
    return {
        "kind": kind,
        "message": message,
        "reconciliation": result.to_dict(),
        "confirmed_repo": result.confirmed_repo,
    }
