# SPDX-License-Identifier: Apache-2.0
"""Provider capability matrix — claimed vs actually wired support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ProviderTier = Literal["full", "expanding", "partial", "stub", "planned"]

@dataclass(frozen=True)
class ProviderCapabilitySummary:
    provider: str
    label: str
    tier: ProviderTier
    e2e_ready: bool
    registered: bool
    readonly_ops: tuple[str, ...] = field(default_factory=tuple)
    mutation_ops: tuple[str, ...] = field(default_factory=tuple)
    gaps: tuple[str, ...] = field(default_factory=tuple)
    honest_summary: str = ""


_PROVIDER_MATRIX: dict[str, ProviderCapabilitySummary] = {
    "railway": ProviderCapabilitySummary(
        provider="railway",
        label="Railway",
        tier="expanding",
        e2e_ready=False,
        registered=True,
        readonly_ops=("health", "logs", "deployments", "service events", "diagnosis"),
        mutation_ops=("restart", "redeploy"),
        gaps=(
            "set_env_var is not enabled on the generic mutation path",
            "production env configure + deploy + verify is not one natural-language E2E flow",
            "greenfield service creation requires deployment plan and execution contract",
            "natural deploy+env chat prompts are not routed to readiness/preflight yet",
        ),
        honest_summary=(
            "Railway is **EXPANDING** — governed restart/redeploy and readonly logs/events are real on "
            "existing services, but env var E2E (especially production) and casual deploy+env chat "
            "orchestration are not complete. Use deployment readiness and governed preflight commands."
        ),
    ),
    "vercel": ProviderCapabilitySummary(
        provider="vercel",
        label="Vercel",
        tier="expanding",
        e2e_ready=False,
        registered=True,
        readonly_ops=(
            "projects",
            "deployments",
            "build/runtime logs",
            "env metadata (keys only)",
            "domains",
        ),
        mutation_ops=("redeploy", "rollback (expanding)", "set/remove env var (expanding)", "promote deployment (expanding)"),
        gaps=(
            "rollback, set_env_var, remove_env_var, and promote_deployment are expanding — not fully wired yet",
            "provider skill layer is still stubbed despite partial adapters",
        ),
        honest_summary=(
            "Vercel is **EXPANDING** — readonly deployments/logs/env metadata and governed redeploy are wired. "
            "Rollback/env mutations and full post-deploy verification are still being hardened."
        ),
    ),
    "github": ProviderCapabilitySummary(
        provider="github",
        label="GitHub",
        tier="expanding",
        e2e_ready=False,
        registered=True,
        readonly_ops=(
            "inspect repo",
            "branch status",
            "recent commits",
            "workflow runs",
            "failed checks",
            "workflow diagnostics/logs",
        ),
        mutation_ops=(
            "workflow_rerun",
            "create branch (expanding)",
            "commit/push (expanding)",
            "open PR (expanding)",
            "cancel workflow (expanding)",
        ),
        gaps=(
            "git push/commit/PR mutations are expanding — governed wiring in progress",
            "PR check verification and outcome learning are expanding",
        ),
        honest_summary=(
            "GitHub is **EXPANDING** — repo/workflow readonly inspection and governed workflow rerun are wired. "
            "Branch/commit/push/PR mutations are planned next under approval gates, not fully executable yet."
        ),
    ),
    "aws": ProviderCapabilitySummary(
        provider="aws",
        label="AWS",
        tier="partial",
        e2e_ready=False,
        registered=True,
        readonly_ops=("ec2 describe", "s3 list buckets", "lambda list (when boto3 installed)"),
        mutation_ops=(),
        gaps=("readonly inventory only", "mutations not enabled on generic path"),
        honest_summary=(
            "AWS is **PARTIAL** — governed readonly inventory via boto3 when credentials and optional "
            "`aethos[cloud]` dependency are present. No mutation E2E path yet."
        ),
    ),
    "gcp": ProviderCapabilitySummary(
        provider="gcp",
        label="GCP",
        tier="partial",
        e2e_ready=False,
        registered=True,
        readonly_ops=("gcloud projects list", "compute instances list"),
        mutation_ops=(),
        gaps=("requires gcloud CLI or Application Default Credentials", "mutations not enabled"),
        honest_summary=(
            "GCP is **PARTIAL** — readonly inventory via `gcloud` when installed and credentialed. "
            "No mutation E2E path yet."
        ),
    ),
    "azure": ProviderCapabilitySummary(
        provider="azure",
        label="Azure",
        tier="partial",
        e2e_ready=False,
        registered=True,
        readonly_ops=("resource groups list", "webapps list"),
        mutation_ops=(),
        gaps=("requires Azure CLI login or service principal env vars", "mutations not enabled"),
        honest_summary=(
            "Azure is **PARTIAL** — readonly inventory via `az` when installed and credentialed. "
            "No mutation E2E path yet."
        ),
    ),
    "kubernetes": ProviderCapabilitySummary(
        provider="kubernetes",
        label="Kubernetes",
        tier="stub",
        e2e_ready=False,
        registered=False,
        readonly_ops=("simulated runtime intelligence only",),
        mutation_ops=(),
        gaps=("no live cluster API adapter", "skill layer is stub-only"),
        honest_summary=(
            "Kubernetes has simulated intelligence modules, not a live governed cluster adapter. "
            "I should not claim full kube execution."
        ),
    ),
}


def get_provider_summary(provider: str) -> ProviderCapabilitySummary | None:
    return _PROVIDER_MATRIX.get((provider or "").strip().lower())


def list_provider_summaries() -> list[ProviderCapabilitySummary]:
    order = ("railway", "vercel", "github", "aws", "gcp", "azure", "kubernetes")
    return [_PROVIDER_MATRIX[name] for name in order if name in _PROVIDER_MATRIX]


def providers_with_e2e_readiness() -> list[ProviderCapabilitySummary]:
    return [summary for summary in list_provider_summaries() if summary.e2e_ready]


def provider_truth_line(summary: ProviderCapabilitySummary) -> str:
    status = summary.tier.upper()
    e2e = "E2E-ready" if summary.e2e_ready else "not E2E-ready"
    return f"- **{summary.label}** ({status}, {e2e}): {summary.honest_summary}"


def provider_display_label(provider: str) -> str:
    summary = get_provider_summary(provider)
    if summary is not None:
        return summary.label
    normalized = (provider or "").strip().lower()
    if normalized == "github":
        return "GitHub"
    if normalized == "gcp":
        return "GCP"
    return (provider or "Provider").strip().title()


def build_provider_matrix_payload() -> dict[str, Any]:
    return {
        "providers": [
            {
                "provider": summary.provider,
                "label": summary.label,
                "tier": summary.tier,
                "e2e_ready": summary.e2e_ready,
                "registered": summary.registered,
                "readonly_ops": list(summary.readonly_ops),
                "mutation_ops": list(summary.mutation_ops),
                "gaps": list(summary.gaps),
                "honest_summary": summary.honest_summary,
            }
            for summary in list_provider_summaries()
        ],
        "e2e_ready_providers": [summary.provider for summary in providers_with_e2e_readiness()],
    }
