# SPDX-License-Identifier: Apache-2.0
"""Governed AethOS durable job types — Phase 11.7.9."""

from __future__ import annotations

from typing import Any

DURABLE_JOB_TYPES: dict[str, dict[str, Any]] = {
    "research_scan": {
        "label": "Evidence research scan",
        "agent_role": "research",
        "readonly": True,
        "requires_approval": False,
        "default_timeout_sec": 900,
    },
    "gtm_synthesis": {
        "label": "Synthesis pass",
        "agent_role": "analysis",
        "readonly": True,
        "requires_approval": False,
        "depends_on": "research_scan",
        "default_timeout_sec": 900,
    },
    "provider_verification": {
        "label": "Provider runtime verification",
        "agent_role": "Provider Operations Agent",
        "readonly": True,
        "requires_approval": False,
        "default_timeout_sec": 300,
    },
    "recovery_window_check": {
        "label": "Recovery verification window",
        "agent_role": "Mission Control Analyst",
        "readonly": True,
        "requires_approval": False,
        "default_timeout_sec": 120,
    },
    "artifact_summarization": {
        "label": "Artifact summarization",
        "agent_role": "Mission Control Analyst",
        "readonly": True,
        "requires_approval": False,
        "default_timeout_sec": 300,
    },
}

MUTATION_JOB_TYPES = frozenset({"provider_restart", "provider_redeploy", "workflow_rerun", "deploy", "rollback"})

BLOCKED_JOB_ACTIONS = frozenset(
    {"auto_merge", "force_push", "unrestricted_shell", "credential_export", "silent_provider_mutation"}
)


def get_job_spec(job_type: str) -> dict[str, Any] | None:
    return DURABLE_JOB_TYPES.get(job_type)


def list_durable_job_types() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in DURABLE_JOB_TYPES.items()]
