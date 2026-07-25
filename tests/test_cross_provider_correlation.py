# SPDX-License-Identifier: Apache-2.0
"""Cross-provider deployment correlation tests."""

from __future__ import annotations

from aethos_core.cross_provider_correlation.commit_identity import commits_match
from aethos_core.cross_provider_correlation.correlation_diagnosis import diagnose_correlation_graph
from aethos_core.cross_provider_correlation.correlation_graph import CorrelationGraph, CorrelationLink
from aethos_core.cross_provider_correlation.correlation_router import route_cross_provider_correlation_question
from aethos_core.cross_provider_correlation.correlation_runtime import run_correlation_analysis
from aethos_core.cross_provider_correlation.correlation_store import clear_store_for_tests, publish_github_evidence, publish_vercel_evidence
from aethos_core.cross_provider_correlation.deployment_identity import DeploymentIdentity
from aethos_core.cross_provider_correlation.evidence_linker import link_cross_provider_evidence
from aethos_core.cross_provider_correlation.provider_identity import ProviderIdentity
from aethos_core.cross_provider_correlation.evidence_publisher import ingest_github_live_evidence, ingest_vercel_live_evidence


def setup_function() -> None:
    clear_store_for_tests()


def _github_evidence(*, status: str = "passed", commit: str = "abc123def456") -> dict:
    workflow = {"ok": True, "latest_failed_run": None}
    checks = {"ok": True, "failed_count": 0}
    if status == "failed":
        workflow = {"ok": True, "latest_failed_run": {"name": "CI", "run_number": 9, "head_branch": "main"}}
        checks = {"ok": True, "failed_count": 1}
    return {
        "repository": "pilotmain/aethos",
        "branch": {"branch": "main", "sha": commit},
        "commits": {"commits": [{"sha": commit, "message": "fix", "author": "raya"}]},
        "checks": checks,
        "workflow_diagnostic": workflow,
    }


def _vercel_evidence(*, status: str = "ready", commit: str = "abc123def456") -> dict:
    state = "ready" if status == "ready" else "error"
    return {
        "project_name": "aethos-web",
        "project": {"details": {"repo_link": "pilotmain/aethos", "production_url": "aethos.vercel.app"}},
        "latest_deployment": {"id": "dpl_1", "state": state, "commit": commit, "branch": "main"},
        "failed_deployment": None if status == "ready" else {"id": "dpl_1", "state": "error", "commit": commit},
        "build_analysis": {"error_lines": ["build failed"] if status != "ready" else []},
    }


def test_commits_match_prefix() -> None:
    assert commits_match("abc123def4567890", "abc123d")


def test_github_commit_matches_vercel_deployment() -> None:
    publish_github_evidence("corr-1", _github_evidence(commit="abc123def456"))
    publish_vercel_evidence("corr-1", _vercel_evidence(commit="abc123def456"))
    graph = link_cross_provider_evidence(
        {
            "github": ProviderIdentity(provider="github", repo="pilotmain/aethos", commit_sha="abc123def456").to_dict(),
            "vercel": DeploymentIdentity(provider="vercel", project="aethos-web", commit_sha="abc123def456").to_dict(),
        },
        session_id="corr-1",
    )
    assert graph.matched_commit.startswith("abc123")
    assert any(link.kind == "commit_sha" for link in graph.links)


def test_github_pass_vercel_fail_boundary_is_vercel() -> None:
    graph = CorrelationGraph(
        session_id="corr-2",
        github=ProviderIdentity(provider="github", repo="pilotmain/aethos", commit_sha="abc123", status="passed"),
        vercel=DeploymentIdentity(provider="vercel", project="aethos-web", commit_sha="abc123", status="failed"),
        links=[CorrelationLink(kind="commit_sha", source="github", target="vercel", confidence=0.95, detail="match")],
        matched_commit="abc123",
        confidence="high",
    )
    diagnosis = diagnose_correlation_graph(graph)
    assert diagnosis.failure_boundary == "vercel"
    assert "GitHub workflow passed" in diagnosis.conclusion


def test_github_fail_vercel_missing_boundary_is_github() -> None:
    graph = CorrelationGraph(
        session_id="corr-3",
        github=ProviderIdentity(provider="github", repo="pilotmain/aethos", commit_sha="abc123", status="failed"),
        vercel=None,
        links=[],
        confidence="low",
    )
    diagnosis = diagnose_correlation_graph(graph)
    assert diagnosis.failure_boundary == "github"
    assert diagnosis.needs_binding or "GitHub" in diagnosis.conclusion


def test_railway_runtime_fail_after_vercel_success() -> None:
    graph = CorrelationGraph(
        session_id="corr-4",
        github=ProviderIdentity(provider="github", repo="pilotmain/aethos", commit_sha="abc123", status="passed"),
        vercel=DeploymentIdentity(provider="vercel", project="aethos-web", commit_sha="abc123", status="ready"),
        railway=DeploymentIdentity(provider="railway", project="pilotcore", service="api", commit_sha="abc123", status="failed"),
        links=[
            CorrelationLink(kind="commit_sha", source="github", target="vercel", confidence=0.95, detail=""),
            CorrelationLink(kind="commit_sha", source="vercel", target="railway", confidence=0.85, detail=""),
        ],
        matched_commit="abc123",
        confidence="high",
    )
    diagnosis = diagnose_correlation_graph(graph)
    assert diagnosis.failure_boundary == "railway"


def test_no_match_requests_binding() -> None:
    reply, meta, _, diagnosis = run_correlation_analysis(session_id="corr-5", intent="push_trace")
    assert diagnosis.needs_binding
    assert meta["failure_boundary"] == "unknown"
    assert "could not correlate" in reply.lower() or "binding" in reply.lower()


def test_push_trace_route_after_evidence_publish() -> None:
    ingest_github_live_evidence("corr-6", _github_evidence(status="passed"))
    ingest_vercel_live_evidence("corr-6", _vercel_evidence(status="ready"))
    result = route_cross_provider_correlation_question("what happened after my latest GitHub push?", session_id="corr-6")
    assert result is not None
    reply, intent, meta = result
    assert intent == "cross_provider_push_trace"
    assert "I traced the latest push across providers" in reply
    assert meta["route_id"] == "cross_provider_correlation"


def test_failure_boundary_route_github_or_vercel() -> None:
    ingest_github_live_evidence("corr-7", _github_evidence(status="passed"))
    ingest_vercel_live_evidence("corr-7", _vercel_evidence(status="failed"))
    result = route_cross_provider_correlation_question("did this deploy fail because of GitHub or Vercel?", session_id="corr-7")
    assert result is not None
    reply, _, meta = result
    assert meta["failure_boundary"] == "vercel"
    assert "vercel" in reply.lower()
