# SPDX-License-Identifier: Apache-2.0
"""Human-centered agentic OS API — Phase 10.0."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["human"])


class VoiceTranscript(BaseModel):
    transcript: str
    session_id: str = "default"
    channel: str = "web_voice"
    action_hint: str | None = None


class ActionProposal(BaseModel):
    action_type: str
    payload: dict[str, Any] | None = None
    session_id: str = "default"


class WorkspaceDocIn(BaseModel):
    doc_id: str | None = None
    title: str | None = None
    content: str | None = None
    format: str | None = None


class WorkspaceNoteIn(BaseModel):
    text: str


class WorkspaceTaskIn(BaseModel):
    text: str
    scheduled_for: str | None = None


class WorkspaceTaskDoneIn(BaseModel):
    done: bool = True


class WorkspaceServeIn(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_id: str
    port: int = 11434


class WorkspaceServeStopIn(BaseModel):
    id: str


class WorkspaceDraftReplyIn(BaseModel):
    to: str
    subject: str = ""
    body: str


class WorkspaceEmailCredentialsIn(BaseModel):
    label: str = ""
    fields: dict[str, str] = {}


class WorkspaceEventIn(BaseModel):
    summary: str
    start: str
    end: str = ""
    description: str = ""
    calendar: str = "default"


class WorkspaceIcsImportIn(BaseModel):
    ics_text: str
    calendar: str = "imported"


class ActionApproval(BaseModel):
    action_id: str
    operator_id: str = "operator"


class CollaborationStart(BaseModel):
    operator_id: str = "default"
    focus: str = "investigation"
    context: str = ""


class LifeOptIn(BaseModel):
    session_id: str = "default"
    domains: list[str] | None = None


class OperatorStyle(BaseModel):
    session_id: str = "default"
    preferred_mode: str = "companion"
    verbosity: str = "medium"


class ChannelInbound(BaseModel):
    channel: str
    payload: dict[str, Any]


@router.get("/human/overview")
def human_overview_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.operational_partner_runtime import get_operational_partner_overview

    return get_operational_partner_overview(session_id=session_id)


@router.get("/human/relational")
def human_relational_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.relational.relational_runtime import get_relational_state

    return get_relational_state(session_id=session_id)


@router.post("/human/relational/style")
def human_relational_style_api(body: OperatorStyle) -> dict[str, Any]:
    from aethos_core.relational.operator_style import set_operator_style

    return {"ok": True, "style": set_operator_style(
        session_id=body.session_id,
        preferred_mode=body.preferred_mode,
        verbosity=body.verbosity,
    )}


@router.get("/human/voice")
def human_voice_api(channel: str = "web_voice") -> dict[str, Any]:
    from aethos_core.voice.voice_runtime import get_voice_status

    return get_voice_status(channel=channel)


@router.post("/human/voice/transcript")
def human_voice_transcript_api(body: VoiceTranscript) -> dict[str, Any]:
    from aethos_core.voice.voice_runtime import process_voice_transcript

    return process_voice_transcript(
        transcript=body.transcript,
        session_id=body.session_id,
        channel=body.channel,
        action_hint=body.action_hint,
    )


@router.get("/human/canvas/{session_id}")
def human_canvas_state_api(session_id: str, limit: int = 20) -> dict[str, Any]:
    """Read-only Live Canvas state for a session (handoff §11). Render surface only."""
    from aethos_core.canvas.canvas_store import get_canvas_state

    return get_canvas_state(session_id=session_id, limit=limit)


@router.get("/human/workspace/documents")
def human_workspace_documents_list_api(limit: int = 100) -> dict[str, Any]:
    """List draft documents (handoff §8). Draft-only; gated by WORKSPACE_SUITE_ENABLED."""
    from aethos_core.workspace_suite.documents_store import list_documents

    return list_documents(limit=limit)


@router.get("/human/workspace/documents/{doc_id}")
def human_workspace_document_get_api(doc_id: str) -> dict[str, Any]:
    from aethos_core.workspace_suite.documents_store import get_document

    return get_document(doc_id=doc_id)


@router.post("/human/workspace/documents")
def human_workspace_document_create_api(body: WorkspaceDocIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.documents_store import create_document

    return create_document(
        title=body.title or "Untitled",
        content=body.content or "",
        fmt=body.format or "markdown",
    )


@router.put("/human/workspace/documents/{doc_id}")
def human_workspace_document_update_api(doc_id: str, body: WorkspaceDocIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.documents_store import update_document

    return update_document(
        doc_id=doc_id,
        title=body.title,
        content=body.content,
        fmt=body.format,
    )


@router.delete("/human/workspace/documents/{doc_id}")
def human_workspace_document_delete_api(doc_id: str) -> dict[str, Any]:
    from aethos_core.workspace_suite.documents_store import delete_document

    return delete_document(doc_id=doc_id)


@router.get("/human/workspace/notes")
def human_workspace_notes_list_api(limit: int = 100) -> dict[str, Any]:
    """List quick notes (handoff §8). Gated by WORKSPACE_SUITE_ENABLED."""
    from aethos_core.workspace_suite.notes_tasks_store import list_notes

    return list_notes(limit=limit)


@router.post("/human/workspace/notes")
def human_workspace_note_add_api(body: WorkspaceNoteIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.notes_tasks_store import add_note

    return add_note(text=body.text)


@router.delete("/human/workspace/notes/{note_id}")
def human_workspace_note_delete_api(note_id: str) -> dict[str, Any]:
    from aethos_core.workspace_suite.notes_tasks_store import delete_note

    return delete_note(note_id=note_id)


@router.get("/human/workspace/tasks")
def human_workspace_tasks_list_api(limit: int = 200) -> dict[str, Any]:
    """List checklist tasks (handoff §8). Scheduled tasks never auto-execute."""
    from aethos_core.workspace_suite.notes_tasks_store import list_tasks

    return list_tasks(limit=limit)


@router.post("/human/workspace/tasks")
def human_workspace_task_add_api(body: WorkspaceTaskIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.notes_tasks_store import add_task

    return add_task(text=body.text, scheduled_for=body.scheduled_for)


@router.put("/human/workspace/tasks/{task_id}/done")
def human_workspace_task_done_api(task_id: str, body: WorkspaceTaskDoneIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.notes_tasks_store import set_task_done

    return set_task_done(task_id=task_id, done=body.done)


@router.delete("/human/workspace/tasks/{task_id}")
def human_workspace_task_delete_api(task_id: str) -> dict[str, Any]:
    from aethos_core.workspace_suite.notes_tasks_store import delete_task

    return delete_task(task_id=task_id)


@router.get("/human/workspace/foundry/scan")
def human_workspace_foundry_scan_api() -> dict[str, Any]:
    """Readonly local hardware scan (handoff §8). Requires MODEL_FOUNDRY_ENABLED."""
    from aethos_core.workspace_suite.model_foundry import scan_hardware

    return scan_hardware()


@router.get("/human/workspace/foundry/recommend")
def human_workspace_foundry_recommend_api() -> dict[str, Any]:
    from aethos_core.workspace_suite.model_foundry import recommend_models

    return recommend_models()


@router.post("/human/workspace/foundry/serve")
def human_workspace_foundry_serve_api(body: WorkspaceServeIn) -> dict[str, Any]:
    """Record a GOVERNED serve request (loopback only). Never auto-serves."""
    from aethos_core.workspace_suite.model_foundry import create_serve_preflight

    return create_serve_preflight(model_id=body.model_id, port=body.port)


@router.get("/human/workspace/foundry/serve-status")
def human_workspace_foundry_serve_status_api() -> dict[str, Any]:
    """Live serve-request status (pending_approval → served → stopped)."""
    from aethos_core.workspace_suite.model_foundry import serve_status_payload

    return serve_status_payload()


@router.post("/human/workspace/foundry/stop")
def human_workspace_foundry_stop_api(body: WorkspaceServeStopIn) -> dict[str, Any]:
    """Record a GOVERNED stop; removes the served model from the chat picker."""
    from aethos_core.workspace_suite.model_foundry import stop_serve

    return stop_serve(req_id=body.id)


@router.post("/human/workspace/foundry/dismiss")
def human_workspace_foundry_dismiss_api(body: WorkspaceServeStopIn) -> dict[str, Any]:
    """Dismiss a pending (un-executed) serve request — clears stacked rows."""
    from aethos_core.workspace_suite.model_foundry import dismiss_serve_request

    return dismiss_serve_request(body.id)


@router.get("/human/workspace/email/connection")
def human_workspace_email_connection_api() -> dict[str, Any]:
    """Per-tenant IMAP credential schema + vault status (workspace email inbox)."""
    from aethos_core.workspace_suite.email_credentials import email_connection_payload

    return email_connection_payload()


@router.post("/human/workspace/email/credentials")
def human_workspace_email_credentials_store_api(body: WorkspaceEmailCredentialsIn) -> dict[str, Any]:
    from aethos_core.security.secret_redaction import redact_text
    from aethos_core.workspace_suite.email_credentials import (
        EmailCredentialError,
        email_connection_payload,
        store_email_imap_credentials,
        test_email_imap_credential,
    )

    try:
        record = store_email_imap_credentials(label=body.label, fields=body.fields)
    except EmailCredentialError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=redact_text(str(exc))) from None
    except Exception as exc:  # noqa: BLE001
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=redact_text(str(exc))[:240]) from None
    try:
        test_result = test_email_imap_credential(record.credential_id)
    except Exception as exc:  # noqa: BLE001
        test_result = {"ok": False, "detail": redact_text(str(exc))}
    return {
        "ok": True,
        "credential": record.to_public_dict(),
        "test": test_result,
        "connection": email_connection_payload(),
    }


@router.post("/human/workspace/email/credentials/{credential_id}/test")
def human_workspace_email_credentials_test_api(credential_id: str) -> dict[str, Any]:
    from fastapi import HTTPException

    from aethos_core.workspace_suite.email_credentials import test_email_imap_credential

    try:
        result = test_email_imap_credential(credential_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Credential not found") from None
    return {"ok": True, "test": result}


@router.post("/human/workspace/email/credentials/{credential_id}/revoke")
def human_workspace_email_credentials_revoke_api(credential_id: str) -> dict[str, Any]:
    from fastapi import HTTPException

    from aethos_core.workspace_suite.email_credentials import (
        email_connection_payload,
        revoke_email_imap_credential,
    )

    if not revoke_email_imap_credential(credential_id):
        raise HTTPException(status_code=404, detail="Credential not found") from None
    return {"ok": True, "revoked": True, "connection": email_connection_payload()}


@router.get("/human/workspace/email/triage")
def human_workspace_email_triage_api(limit: int = 20) -> dict[str, Any]:
    """Readonly IMAP inbox triage (handoff §8). Requires WORKSPACE_SUITE_ENABLED + IMAP creds."""
    from aethos_core.workspace_suite.email_triage import triage_inbox

    return triage_inbox(limit=limit)


@router.get("/human/workspace/email/drafts")
def human_workspace_email_drafts_api(limit: int = 50) -> dict[str, Any]:
    from aethos_core.workspace_suite.email_triage import list_draft_replies

    return list_draft_replies(limit=limit)


@router.post("/human/workspace/email/drafts")
def human_workspace_email_draft_create_api(body: WorkspaceDraftReplyIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.email_triage import create_draft_reply

    return create_draft_reply(to=body.to, subject=body.subject, body=body.body)


@router.post("/human/workspace/email/drafts/{draft_id}/send-preflight")
def human_workspace_email_send_preflight_api(draft_id: str) -> dict[str, Any]:
    """Route a draft into the governed outbound email preflight (never auto-sends)."""
    from aethos_core.workspace_suite.email_triage import send_draft_preflight

    return send_draft_preflight(draft_id=draft_id)


@router.get("/human/workspace/calendar/events")
def human_workspace_calendar_events_api(limit: int = 200) -> dict[str, Any]:
    """List local calendar events (handoff §8). Requires WORKSPACE_SUITE_ENABLED."""
    from aethos_core.workspace_suite.calendar_store import list_events

    return list_events(limit=limit)


@router.post("/human/workspace/calendar/events")
def human_workspace_calendar_event_add_api(body: WorkspaceEventIn) -> dict[str, Any]:
    """Add a LOCAL event (does not write to a remote calendar)."""
    from aethos_core.workspace_suite.calendar_store import add_event

    return add_event(
        summary=body.summary,
        start=body.start,
        end=body.end,
        description=body.description,
        calendar=body.calendar,
    )


@router.delete("/human/workspace/calendar/events/{event_id}")
def human_workspace_calendar_event_delete_api(event_id: str) -> dict[str, Any]:
    from aethos_core.workspace_suite.calendar_store import delete_event

    return delete_event(event_id=event_id)


@router.post("/human/workspace/calendar/import")
def human_workspace_calendar_import_api(body: WorkspaceIcsImportIn) -> dict[str, Any]:
    from aethos_core.workspace_suite.calendar_store import import_ics

    return import_ics(ics_text=body.ics_text, calendar=body.calendar)


@router.get("/human/workspace/calendar/export")
def human_workspace_calendar_export_api() -> dict[str, Any]:
    from aethos_core.workspace_suite.calendar_store import export_ics

    return export_ics()


@router.post("/human/workspace/calendar/sync")
def human_workspace_calendar_sync_api() -> dict[str, Any]:
    """Readonly CalDAV sync (handoff §8). Degrades to caldav_not_configured."""
    from aethos_core.workspace_suite.calendar_store import caldav_sync

    return caldav_sync()


@router.get("/human/channels")
def human_channels_api() -> dict[str, Any]:
    from aethos_core.channels.universal.universal_channel_runtime import list_universal_channels

    return list_universal_channels()


@router.post("/human/channels/inbound")
def human_channel_inbound_api(body: ChannelInbound) -> dict[str, Any]:
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound

    return route_channel_inbound(channel=body.channel, payload=body.payload)


@router.get("/human/life")
def human_life_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.life.life_runtime import get_lifeos_status

    return get_lifeos_status(session_id=session_id)


@router.post("/human/life/opt-in")
def human_life_opt_in_api(body: LifeOptIn) -> dict[str, Any]:
    from aethos_core.life.life_runtime import opt_in_lifeos

    return opt_in_lifeos(session_id=body.session_id, domains=body.domains)


@router.post("/human/life/revoke")
def human_life_revoke_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.life.life_runtime import revoke_lifeos

    return revoke_lifeos(session_id=session_id)


@router.get("/human/actions")
def human_actions_api(session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.action_runtime.action_runtime import list_pending_actions

    return list_pending_actions(session_id=session_id)


@router.post("/human/actions/propose")
def human_action_propose_api(body: ActionProposal) -> dict[str, Any]:
    from aethos_core.action_runtime.action_runtime import propose_action

    return propose_action(action_type=body.action_type, payload=body.payload, session_id=body.session_id)


@router.post("/human/actions/approve")
def human_action_approve_api(body: ActionApproval) -> dict[str, Any]:
    from aethos_core.action_runtime.action_runtime import approve_action

    return approve_action(action_id=body.action_id, operator_id=body.operator_id)


@router.get("/human/ambient")
def human_ambient_api(session_id: str = "default", window_hours: int = 8) -> dict[str, Any]:
    from aethos_core.presence.ambient_presence import build_while_you_were_away, get_ambient_presence_status

    return {
        "status": get_ambient_presence_status(session_id=session_id),
        "away_brief": build_while_you_were_away(window_hours=window_hours, session_id=session_id),
    }


@router.get("/human/collaboration")
def human_collaboration_api(operator_id: str | None = None) -> dict[str, Any]:
    from aethos_core.collaboration.collaboration_runtime import list_collaboration_sessions

    return list_collaboration_sessions(operator_id=operator_id)


@router.post("/human/collaboration/start")
def human_collaboration_start_api(body: CollaborationStart) -> dict[str, Any]:
    from aethos_core.collaboration.collaboration_runtime import start_collaboration_session

    return start_collaboration_session(operator_id=body.operator_id, focus=body.focus, context=body.context)


@router.get("/human/trust")
def human_trust_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.trust.trust_leadership import build_trust_center

    return build_trust_center(session_id=session_id)


@router.get("/human/marketplace")
def human_marketplace_api() -> dict[str, Any]:
    from aethos_sdk.plugin_registry import list_plugins

    return {"ok": True, "plugins": list_plugins(), "sandboxed": True, "permission_scoped": True, "audited": True}


@router.get("/human/mobile-edge")
def human_mobile_edge_api() -> dict[str, Any]:
    from aethos_core.pwa.web_push import pwa_status
    from aethos_core.runtime.edge_runtime import get_edge_runtime_status, get_hosted_cloud_status

    return {"edge": get_edge_runtime_status(), "hosted": get_hosted_cloud_status(), "pwa": pwa_status()}


@router.get("/human/living")
def human_living_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.living_companion_runtime import get_living_companion_overview

    return get_living_companion_overview(session_id=session_id)


@router.get("/human/live-presence")
def human_live_presence_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.live.live_presence_runtime import (
        build_contextual_nudge,
        get_live_operational_stream,
        get_live_presence_status,
    )

    return {
        "status": get_live_presence_status(session_id=session_id),
        "stream": get_live_operational_stream(session_id=session_id),
        "nudge": build_contextual_nudge(session_id=session_id),
    }


@router.get("/human/conversation")
def human_conversation_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.conversation.conversation_runtime import get_conversation_status, resume_conversation

    return {"status": get_conversation_status(session_id=session_id), "resume": resume_conversation(session_id=session_id)}


@router.get("/human/copilot")
def human_copilot_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.copilot.copilot_runtime import generate_operational_hypotheses, get_copilot_status, rank_recommendations

    return {
        "status": get_copilot_status(session_id=session_id),
        "hypotheses": generate_operational_hypotheses(session_id=session_id),
        "recommendations": rank_recommendations(session_id=session_id),
    }


@router.get("/human/personal")
def human_personal_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.personal_intelligence.personal_runtime import get_personal_intelligence_status

    return get_personal_intelligence_status(session_id=session_id)


@router.post("/human/personal/opt-in")
def human_personal_opt_in_api(session_id: str = "default", explanation_style: str = "balanced") -> dict[str, Any]:
    from aethos_core.personal_intelligence.personal_runtime import opt_in_personal_intelligence

    return opt_in_personal_intelligence(session_id=session_id, explanation_style=explanation_style)


@router.post("/human/personal/delete")
def human_personal_delete_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.personal_intelligence.personal_runtime import delete_personal_intelligence

    return delete_personal_intelligence(session_id=session_id)


@router.get("/human/thinking-boundaries")
def human_thinking_boundaries_api(capability: str | None = None) -> dict[str, Any]:
    from aethos_core.human_centered.thinking_boundaries import assess_thinking_boundaries

    return assess_thinking_boundaries(proposed_capability=capability)


@router.get("/human/explainability")
def human_explainability_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.trust.world_class_explainability import build_world_class_explanation

    return build_world_class_explanation(session_id=session_id)


@router.get("/human/teamwork")
def human_teamwork_api(operator_id: str | None = None) -> dict[str, Any]:
    from aethos_core.collaboration.teamwork_runtime import list_collaboration_rooms

    return list_collaboration_rooms(operator_id=operator_id)


@router.post("/human/teamwork/room")
def human_teamwork_room_api(operator_id: str = "default", title: str = "Investigation", focus: str = "debugging") -> dict[str, Any]:
    from aethos_core.collaboration.teamwork_runtime import create_collaboration_room

    return create_collaboration_room(operator_id=operator_id, title=title, focus=focus)


@router.get("/human/multimodal-voice")
def human_multimodal_voice_api(channel: str = "web_voice") -> dict[str, Any]:
    from aethos_core.voice.multimodal_runtime import get_multimodal_voice_status

    return get_multimodal_voice_status(channel=channel)


@router.get("/human/routes")
def human_routes_discovery_api() -> dict[str, Any]:
    from aethos_core.human_centered.human_route_registry import discover_human_routes

    return discover_human_routes()


@router.get("/human/integrity")
def human_runtime_integrity_api() -> dict[str, Any]:
    from aethos_core.runtime.runtime_integrity.runtime_health import build_runtime_integrity_report

    return build_runtime_integrity_report()


@router.get("/human/replay")
def human_runtime_replay_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.human_runtime_replay import get_human_runtime_replay

    return get_human_runtime_replay(session_id=session_id)


@router.get("/human/continuity")
def human_continuity_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.conversation.continuity_renderer import render_continuity_resume
    from aethos_core.human_centered.continuity_memory import get_continuity_transparency

    return {
        "memory": get_continuity_transparency(session_id=session_id),
        "resume": render_continuity_resume(session_id=session_id),
    }


@router.get("/human/trust-controls")
def human_trust_controls_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.trust_controls import get_trust_controls

    return get_trust_controls(session_id=session_id)


@router.post("/human/trust-controls/delete-memory")
def human_delete_operator_memory_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.trust_controls import delete_all_operator_memory

    return delete_all_operator_memory(session_id=session_id)


@router.get("/human/intuition")
def human_intuition_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.intuition.intuition_engine import assess_operational_intuition

    return assess_operational_intuition(session_id=session_id)


@router.get("/human/companion-brief")
def human_companion_brief_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.operational_partner_runtime import render_operational_partner_brief

    return render_operational_partner_brief(session_id=session_id)


@router.get("/human/partner-brief")
def human_partner_brief_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.operational_partner_runtime import render_operational_partner_brief

    return render_operational_partner_brief(session_id=session_id)


@router.get("/human/operational-reasoning")
def human_operational_reasoning_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.reasoning.reasoning_engine import assess_deep_operational_reasoning

    return assess_deep_operational_reasoning(session_id=session_id)


@router.get("/human/investigation-companion")
def human_investigation_companion_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.collaboration.investigation.investigation_companion import build_investigation_companion_brief

    return build_investigation_companion_brief(session_id=session_id)


@router.get("/human/deep-replay")
def human_deep_replay_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.replay.deep_replay.deep_replay_runtime import get_deep_replay_intelligence

    return get_deep_replay_intelligence(session_id=session_id)


@router.get("/human/emotional-realism")
def human_emotional_realism_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.emotional_realism.emotional_realism_runtime import assess_emotional_realism

    return assess_emotional_realism(session_id=session_id)


@router.get("/human/attention-awareness")
def human_attention_awareness_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.attention.attention_awareness import assess_operator_attention

    return assess_operator_attention(session_id=session_id)


@router.get("/human/companion-narrative")
def human_companion_narrative_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.narrative.companion_narrative import build_companion_narrative

    return build_companion_narrative(session_id=session_id)


@router.get("/human/companion-quality")
def human_companion_quality_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.intuition.companion_quality_metrics import compute_companion_quality_metrics

    return compute_companion_quality_metrics(session_id=session_id)


@router.get("/human/restraint-v2")
def human_restraint_v2_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.restraint.restraint_v2 import get_restraint_v2_status

    return get_restraint_v2_status(session_id=session_id)


@router.get("/human/presence-quality")
def human_presence_quality_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.intuition.presence_quality_metrics import compute_presence_quality_metrics

    return compute_presence_quality_metrics(session_id=session_id)


@router.get("/human/calm-presence")
def human_calm_presence_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.calm.calm_presence_runtime import get_calm_presence_state

    return get_calm_presence_state(session_id=session_id)


@router.get("/human/timeline")
def human_timeline_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.timeline.operational_timeline import get_operational_narrative

    return get_operational_narrative(session_id=session_id)


@router.get("/human/living-explainability")
def human_living_explainability_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.trust.living_explainability import get_living_explainability

    return get_living_explainability(session_id=session_id)


@router.get("/human/restraint")
def human_restraint_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.restraint.restraint_runtime import get_restraint_status

    return get_restraint_status(session_id=session_id)


@router.get("/conversational-intelligence/state")
def conversational_intelligence_state_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_conversational_intelligence

    return assess_conversational_intelligence()


@router.get("/conversational-intelligence/harness/scenarios")
def synthesis_harness_scenarios_api() -> dict[str, Any]:
    from aethos_core.synthesis_harness.harness_runtime import harness_state

    return harness_state()


@router.post("/conversational-intelligence/synthesize")
def conversational_synthesize_api(body: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import ensure_reliable_response

    return ensure_reliable_response(
        query=str(body.get("query") or ""),
        evidence=body.get("evidence"),
        raw_reply=str(body.get("raw_reply") or ""),
        overall_confidence=float(body.get("overall_confidence") or 0.6),
        mode=str(body.get("mode") or "casual"),
        include_followups=bool(body.get("include_followups", False)),
    )


@router.get("/conversational-reliability/state")
def conversational_reliability_state_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_production_conversational_qualification

    return assess_production_conversational_qualification()


@router.get("/conversational-qualification/state")
def conversational_qualification_state_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_production_conversational_qualification

    return assess_production_conversational_qualification()


@router.get("/conversational-reliability/harness/scenarios")
def conversational_reliability_harness_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import harness_state

    return harness_state()


@router.get("/conversational-convergence/state")
def conversational_convergence_state_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_conversational_convergence

    return assess_conversational_convergence()


@router.get("/conversational-convergence/layers")
def conversational_convergence_layers_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import describe_interaction_layers

    return describe_interaction_layers()


@router.get("/conversational-operational-grounding/state")
def conversational_operational_grounding_state_api(session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding

    return assess_conversational_operational_grounding(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/continuity-reconstruction")
def conversational_continuity_reconstruction_api(session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread

    return {"ok": True, **reconstruct_operational_thread(session_id=session_id, channel=channel)}


@router.get("/conversational-operational-grounding/operational-context")
def conversational_operational_context_api(session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge

    return {"ok": True, **build_operational_context_bridge(session_id=session_id, channel=channel)}


@router.get("/conversational-operational-grounding/governance-restraint")
def conversational_governance_restraint_api(channel: str = "chat") -> dict[str, Any]:
    from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint

    return {"ok": True, **assess_governance_restraint(channel=channel, grounded=True)}


@router.get("/conversational-operational-grounding/conversational-realism")
def conversational_realism_api() -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_conversational_realism

    return {"ok": True, **assess_conversational_realism()}


@router.get("/conversational-operational-grounding/telegram-persistence")
def conversational_telegram_persistence_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.telegram_session_persistence.session_bridge import hydrate_telegram_session

    return {"ok": True, **hydrate_telegram_session(session_id=session_id)}


@router.get("/conversational-operational-grounding/partner-presence")
def conversational_partner_presence_api(session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    from aethos_core.operational_partner_presence.partner_runtime import assess_operational_partner_presence

    return assess_operational_partner_presence(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/live-operational-grounding")
def conversational_live_operational_grounding_api(
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    from aethos_core.live_operational_grounding.runtime import assess_live_operational_grounding

    return assess_live_operational_grounding(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/operational-entity-runtime")
def conversational_operational_entity_runtime_api(
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    from aethos_core.operational_entity_runtime.runtime import assess_operational_entity_runtime

    return assess_operational_entity_runtime(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/operational-progression-runtime")
def conversational_operational_progression_runtime_api(
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    from aethos_core.operational_progression_runtime.runtime import assess_operational_progression_runtime

    return assess_operational_progression_runtime(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/investigative-continuity-runtime")
def conversational_investigative_continuity_runtime_api(
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    from aethos_core.investigative_continuity_runtime.runtime import assess_investigative_continuity_runtime

    return assess_investigative_continuity_runtime(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/cross-surface-convergence")
def conversational_cross_surface_convergence_api(
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    from aethos_core.cross_surface_reality_convergence.runtime import assess_cross_surface_reality_convergence

    return assess_cross_surface_reality_convergence(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/cross-surface")
def conversational_cross_surface_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.operational_context_memory.cross_surface_bridge import merge_cross_surface_context

    return {"ok": True, **merge_cross_surface_context(session_id=session_id)}


@router.get("/conversational-operational-grounding/thread-integrity")
def conversational_thread_integrity_api(session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    from aethos_core.operational_thread_integrity.runtime import assess_operational_thread_integrity

    return assess_operational_thread_integrity(session_id=session_id, channel=channel)


@router.get("/conversational-operational-grounding/realism-polish")
def conversational_realism_polish_api(
    session_id: str = "default",
    channel: str = "chat",
    confidence: float = 0.6,
) -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import assess_conversational_realism_polish

    return assess_conversational_realism_polish(session_id=session_id, channel=channel, confidence=confidence)


@router.post("/conversational-operational-grounding/synthesize")
def conversational_grounding_synthesize_api(body: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.conversation.legacy_polish_api import synthesize_grounded_operational_reply

    result = synthesize_grounded_operational_reply(
        user_text=str(body.get("query") or ""),
        session_id=str(body.get("session_id") or "default"),
        channel=str(body.get("channel") or "chat"),
    )
    return {"ok": True, **(result or {"grounded": False})}
