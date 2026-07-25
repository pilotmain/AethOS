# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import VercelInventoryArtifact, VercelProject
from aethos_core.browser.platforms.vercel.vercel_inventory_builder import (
    build_chat_summary_bullets,
    build_operational_summary,
    inventory_confidence_lines,
)


def test_all_confirmed_uses_single_line():
    artifact = VercelInventoryArtifact(
        projects=[
            VercelProject(name="a", environment="production"),
            VercelProject(name="b", environment="production"),
        ],
        extraction_method="dom",
    )
    lines = inventory_confidence_lines(artifact)
    assert len(lines) == 1
    assert "confirmed" in lines[0].lower()
    bullets = build_chat_summary_bullets(artifact)
    assert "confirmed vercel project" in bullets.lower()
    summary = build_operational_summary(artifact)
    assert "confirmed vercel project" in summary.lower()


def test_mixed_confirmed_and_likely_matches_chat_and_report():
    artifact = VercelInventoryArtifact(
        projects=[
            VercelProject(name="confirmed-one", environment="production"),
            VercelProject(name="likely-one", environment="likely"),
        ],
        likely_project_names=["likely-one"],
        extraction_method="dom",
    )
    lines = inventory_confidence_lines(artifact)
    assert any("1" in ln and "confirmed" in ln for ln in lines)
    assert any("likely" in ln for ln in lines)
    bullets = build_chat_summary_bullets(artifact)
    summary = build_operational_summary(artifact)
    assert "confirmed" in bullets.lower()
    assert "likely" in bullets.lower()
    assert "confirmed" in summary.lower()
    assert "likely" in summary.lower()
