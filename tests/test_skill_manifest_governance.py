# SPDX-License-Identifier: Apache-2.0
"""Governed skill marketplace (phase 1): skills are parsed into manifests and
risk-classified (read-only vs governed-mutation) so they can be reviewed before
they're trusted — the trust foundation that an open plugin ecosystem lacks."""

from __future__ import annotations

from aethos_core.skills.manifest import (
    governed_skill_catalog,
    parse_skill_manifest,
)

MUTATING = """---
name: deploy-service
description: Deploy a service through the governed preflight flow.
version: 1.2.0
author: aethos
tags: [deploy, provider]
---

## Readonly tools
- validate provider credential

## Mutation tools
- create deploy/redeploy preflight (governed)
- verify_deployment (post-approval)

## Governance
Mutation. Always preflight -> approve -> execute -> verify.
"""

READONLY = """---
name: check-logs
description: Read recent logs for a service.
---

## Readonly tools
- fetch logs
- read deployment status

## Governance
Read-only. No mutations.
"""


def test_parses_frontmatter_and_tools():
    m = parse_skill_manifest("deploy-service", MUTATING)
    assert m.name == "deploy-service"
    assert m.version == "1.2.0"
    assert m.author == "aethos"
    assert "deploy" in m.tags and "provider" in m.tags
    assert any("preflight" in t for t in m.mutation_tools)
    assert "validate provider credential" in m.readonly_tools


def test_mutating_skill_is_governed_and_requires_approval():
    m = parse_skill_manifest("deploy-service", MUTATING)
    assert m.mutates is True
    assert m.risk == "governed-mutation"
    assert m.requires_approval is True


def test_readonly_skill_is_low_risk():
    m = parse_skill_manifest("check-logs", READONLY)
    assert m.mutates is False
    assert m.risk == "read-only"
    assert m.requires_approval is False


def test_governance_detected_even_without_mutation_tools_section():
    content = "---\nname: x\ndescription: y\n---\n\n## Governance\nMutation. Governed.\n"
    m = parse_skill_manifest("x", content)
    assert m.mutates is True and m.risk == "governed-mutation"


def test_catalog_classifies_installed_skills_with_summary():
    cat = governed_skill_catalog()
    assert cat["ok"] is True
    assert cat["count"] >= 1  # repo ships operator skills (deploy-service, check-logs, …)
    risks = {s["risk"] for s in cat["skills"]}
    assert risks <= {"read-only", "governed-mutation"}
    # The repo's deploy/restart/rollback skills are mutating → governed.
    assert cat["summary"]["governed_mutation"] >= 1
    ids = {s["id"] for s in cat["skills"]}
    assert "deploy-service" in ids
    deploy = next(s for s in cat["skills"] if s["id"] == "deploy-service")
    assert deploy["requires_approval"] is True
