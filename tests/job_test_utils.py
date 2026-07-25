# SPDX-License-Identifier: Apache-2.0
"""Helpers for async provider job tests."""

from __future__ import annotations


def drain_job_executor(max_rounds: int = 20) -> None:
    from aethos_core.runtime.job_executor import job_executor

    for _ in range(max_rounds):
        if not job_executor.drain_once_for_tests():
            break


def mock_provider_job_result(
    text: str,
    *,
    provider: str = "none",
    model: str = "template",
    used_llm: bool = False,
    fallback: bool = True,
    job_type: str = "research_plan",
    title: str = "Test",
):
    """Build a ProviderJobResult with artifact fields for tests."""
    from aethos_core.runtime.job_artifacts import build_artifact_bundle
    from aethos_core.runtime.provider_job_runner import ProviderJobResult

    bundle = build_artifact_bundle(text, job_type=job_type, title=title)
    return ProviderJobResult(
        full_result=bundle.full_result,
        summary=bundle.summary,
        preview=bundle.preview,
        provider=provider,
        model=model,
        used_llm=used_llm,
        fallback=fallback,
    )
