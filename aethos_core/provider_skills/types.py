# SPDX-License-Identifier: Apache-2.0
"""Provider skill shared types — governed execution plans and evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderExecutionPlan:
    provider: str
    operation: str
    target_name: str
    execution_mode: str
    command: str | None = None
    command_args: list[str] = field(default_factory=list)
    graphql_operation: str | None = None
    mutation_variables: dict[str, Any] = field(default_factory=dict)
    service_id: str | None = None
    project_id: str | None = None
    environment_id: str | None = None
    deployment_id: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "target_name": self.target_name,
            "execution_mode": self.execution_mode,
            "command": self.command,
            "command_args": list(self.command_args),
            "graphql_operation": self.graphql_operation,
            "mutation_variables": dict(self.mutation_variables),
            "service_id": self.service_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
            "deployment_id": self.deployment_id,
            "diagnostics": dict(self.diagnostics),
            "requires_approval": self.requires_approval,
        }


@dataclass
class ProviderDryRunEvidence:
    ok: bool
    plan: ProviderExecutionPlan
    detail: str
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "plan": self.plan.to_dict(),
            "detail": self.detail,
            "issues": list(self.issues),
        }


@dataclass
class ProviderExecutionResult:
    ok: bool
    command_submitted: bool
    provider: str
    operation: str
    target_name: str
    execution_mode: str
    command: str | None = None
    provider_response: dict[str, Any] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    logs_before: list[dict[str, Any]] = field(default_factory=list)
    logs_after: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "command_submitted": self.command_submitted,
            "provider": self.provider,
            "operation": self.operation,
            "target_name": self.target_name,
            "execution_mode": self.execution_mode,
            "command": self.command,
            "provider_response": dict(self.provider_response),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "before": dict(self.before),
            "after": dict(self.after),
            "logs_before": list(self.logs_before),
            "logs_after": list(self.logs_after),
        }


@dataclass
class ProviderEvidenceBundle:
    operation: str
    provider: str
    target: str
    approved_at: str | None
    command: str | None
    command_submitted: bool
    execution_mode: str
    provider_response: dict[str, Any] = field(default_factory=dict)
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    logs_excerpt: list[dict[str, Any]] = field(default_factory=list)
    diagnosis: dict[str, Any] | None = None
    fix_plan: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "provider": self.provider,
            "target": self.target,
            "approved_at": self.approved_at,
            "command": self.command,
            "command_submitted": self.command_submitted,
            "execution_mode": self.execution_mode,
            "provider_response": dict(self.provider_response),
            "before": dict(self.before),
            "after": dict(self.after),
            "evidence": dict(self.evidence),
            "verification": dict(self.verification),
            "logs_excerpt": list(self.logs_excerpt),
            "diagnosis": self.diagnosis,
            "fix_plan": self.fix_plan,
        }


@dataclass
class ProviderVerificationResult:
    status: str
    verified: bool
    confidence: str
    reason: str
    state: str
    checks: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "verified": self.verified,
            "confidence": self.confidence,
            "reason": self.reason,
            "state": self.state,
            "checks": list(self.checks),
        }


@dataclass
class ProviderDiagnosis:
    ok: bool
    category: str
    summary: str
    likely_cause: str
    log_signals: list[str] = field(default_factory=list)
    suggested_operation: str | None = None
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "category": self.category,
            "summary": self.summary,
            "likely_cause": self.likely_cause,
            "log_signals": list(self.log_signals),
            "suggested_operation": self.suggested_operation,
            "requires_approval": self.requires_approval,
        }


@dataclass
class ProviderFixPlan:
    ok: bool
    summary: str
    proposed_operation: str | None = None
    proposed_changes: list[str] = field(default_factory=list)
    requires_approval: bool = True
    preflight_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "proposed_operation": self.proposed_operation,
            "proposed_changes": list(self.proposed_changes),
            "requires_approval": self.requires_approval,
            "preflight_required": self.preflight_required,
        }
