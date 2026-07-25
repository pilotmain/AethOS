# SPDX-License-Identifier: Apache-2.0
"""FIX 126 — Phase 2 software delivery certification freeze."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from aethos_core.phase.aethos_phase_2_readiness_contract import (
    CERTIFY_EXPECTED_MIN_TESTS_FIX_124,
    CERTIFY_TEST_MODULE_COUNT_FIX_124,
    SOFTWARE_DELIVERY_FIX_125A_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125B_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125C_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125D_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125E_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125F_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125G_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125H_SHIPPED,
    SOFTWARE_DELIVERY_FIX_125I_SHIPPED,
    SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX,
    SOFTWARE_DELIVERY_PHASE_2_FROZEN,
)
from aethos_core.software_delivery.branch_orchestration_contract import (
    MERGE_ENABLED_FIX_125B,
)
from aethos_core.software_delivery.branch_push_contract import (
    GITHUB_PR_CREATE_ENABLED_FIX_125H,
)
from aethos_core.software_delivery.github_pr_open_contract import (
    DEPLOY_ENABLED_FIX_125I,
    GITHUB_PR_OPEN_APPROVAL_PHRASE,
    MERGE_ENABLED_FIX_125I,
    RAILWAY_MUTATION_ENABLED_FIX_125I,
)
from aethos_core.software_delivery.github_pr_open_service import (
    _validate_pr_open_gates,
)
from aethos_core.software_delivery.github_pr_preflight_contract import (
    GIT_PUSH_ENABLED_FIX_125G,
)
from aethos_core.software_delivery.issue_plan_contract import (
    INFRA_MUTATION_PERMITTED,
    SOFTWARE_DELIVERY_LANE_ID,
)
from aethos_core.software_delivery.software_delivery_phase_2_contract import (
    SOFTWARE_DELIVERY_APPROVAL_PHRASES,
    SOFTWARE_DELIVERY_CERTIFIED_STAGES,
    SOFTWARE_DELIVERY_DEFERRED_AFTER_FREEZE,
    SOFTWARE_DELIVERY_FIX_RANGE,
    SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES,
    SOFTWARE_DELIVERY_FROZEN_COMMIT_REF,
    SOFTWARE_DELIVERY_FROZEN_INVARIANTS,
    SOFTWARE_DELIVERY_FROZEN_LANES,
    SOFTWARE_DELIVERY_LANE_DOC_PATHS,
    SOFTWARE_DELIVERY_LANE_OWNERSHIP_MAP,
    SOFTWARE_DELIVERY_LOOP_FIX_MAP,
    SOFTWARE_DELIVERY_LOOP_ORDER,
    SOFTWARE_DELIVERY_MERGE_ENABLED,
    SOFTWARE_DELIVERY_MIN_CERT_MODULES,
    SOFTWARE_DELIVERY_MIN_TEST_COUNT,
    SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX as SD_CONTRACT_FREEZE_FIX,
    SOFTWARE_DELIVERY_PHASE_2_FROZEN as SD_CONTRACT_FROZEN,
    SOFTWARE_DELIVERY_ROUTE_ID,
    SOFTWARE_DELIVERY_SHIPPED_FIXES,
)

pytestmark = pytest.mark.certification

REPO_ROOT = Path(__file__).resolve().parents[2]
SD_ROOT = REPO_ROOT / "aethos_core" / "software_delivery"


def _certify_modules_from_makefile() -> list[str]:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    for line in makefile.splitlines():
        if "tests/certification/test_aethos_core_certification.py" in line:
            return [part for part in line.split() if part.startswith("tests/certification/")]
    raise AssertionError("certify target not found in Makefile")


class TestSoftwareDeliveryPhase2FrozenContract:
    def test_freeze_identity(self) -> None:
        assert SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX == "FIX 126"
        assert SD_CONTRACT_FREEZE_FIX == "FIX 126"
        assert SOFTWARE_DELIVERY_PHASE_2_FROZEN is True
        assert SD_CONTRACT_FROZEN is True
        assert SOFTWARE_DELIVERY_FIX_RANGE == "FIX 125A–FIX 125I"
        assert len(SOFTWARE_DELIVERY_FROZEN_COMMIT_REF) >= 7

    def test_certification_minimums(self) -> None:
        assert SOFTWARE_DELIVERY_MIN_CERT_MODULES == 19
        assert SOFTWARE_DELIVERY_MIN_TEST_COUNT == 61
        modules = _certify_modules_from_makefile()
        assert len(modules) >= SOFTWARE_DELIVERY_MIN_CERT_MODULES
        assert CERTIFY_TEST_MODULE_COUNT_FIX_124 >= SOFTWARE_DELIVERY_MIN_CERT_MODULES
        assert CERTIFY_EXPECTED_MIN_TESTS_FIX_124 >= SOFTWARE_DELIVERY_MIN_TEST_COUNT

    def test_loop_order_frozen(self) -> None:
        assert SOFTWARE_DELIVERY_LOOP_ORDER == (
            "issue_intake",
            "implementation_plan",
            "implementation_branch",
            "patch_proposal",
            "workspace_apply",
            "workspace_verify",
            "pr_draft",
            "github_pr_preflight",
            "branch_push",
            "pr_open",
            "human_review",
        )
        assert len(SOFTWARE_DELIVERY_FROZEN_LANES) == 9
        assert len(SOFTWARE_DELIVERY_LOOP_FIX_MAP) == len(SOFTWARE_DELIVERY_LOOP_ORDER)

    def test_lane_ownership_map(self) -> None:
        assert SOFTWARE_DELIVERY_LANE_OWNERSHIP_MAP["unified_router"].endswith(
            "software_delivery_router"
        )
        for lane in SOFTWARE_DELIVERY_FROZEN_LANES:
            assert lane in SOFTWARE_DELIVERY_LANE_OWNERSHIP_MAP

    def test_frozen_invariants(self) -> None:
        assert "governed_workspace_only" in SOFTWARE_DELIVERY_FROZEN_INVARIANTS
        assert "no_merge" in SOFTWARE_DELIVERY_FROZEN_INVARIANTS
        assert "rollback_snapshots_mandatory" in SOFTWARE_DELIVERY_FROZEN_INVARIANTS

    def test_all_subfixes_shipped(self) -> None:
        flags = (
            SOFTWARE_DELIVERY_FIX_125A_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125B_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125C_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125D_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125E_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125F_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125G_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125H_SHIPPED,
            SOFTWARE_DELIVERY_FIX_125I_SHIPPED,
        )
        assert all(flags)
        assert len(SOFTWARE_DELIVERY_SHIPPED_FIXES) == 9

    def test_route_and_stages(self) -> None:
        assert SOFTWARE_DELIVERY_ROUTE_ID == SOFTWARE_DELIVERY_LANE_ID
        assert "github_pr_open" in SOFTWARE_DELIVERY_CERTIFIED_STAGES
        assert "workspace_rollback" in SOFTWARE_DELIVERY_CERTIFIED_STAGES
        assert "github_pr_preflight_run" in SOFTWARE_DELIVERY_CERTIFIED_STAGES

    def test_approval_phrases_required(self) -> None:
        assert GITHUB_PR_OPEN_APPROVAL_PHRASE in SOFTWARE_DELIVERY_APPROVAL_PHRASES
        assert len(SOFTWARE_DELIVERY_APPROVAL_PHRASES) >= 8

    def test_forbidden_capabilities_frozen(self) -> None:
        assert SOFTWARE_DELIVERY_MERGE_ENABLED is False
        assert "auto_merge" in SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES
        assert "railway_mutation" in SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES
        assert MERGE_ENABLED_FIX_125B is False
        assert GIT_PUSH_ENABLED_FIX_125G is False
        assert GITHUB_PR_CREATE_ENABLED_FIX_125H is False
        assert MERGE_ENABLED_FIX_125I is False
        assert DEPLOY_ENABLED_FIX_125I is False
        assert RAILWAY_MUTATION_ENABLED_FIX_125I is False
        assert INFRA_MUTATION_PERMITTED is False

    def test_pr_open_requires_branch_push_gate(self) -> None:
        blockers = _validate_pr_open_gates(
            user_text="",
            plan={"plan_id": "plan-test"},
        )
        assert "branch_push_not_completed" in blockers or "branch_push_missing" in blockers
        assert "github_pr_open_approval_required" in blockers

    def test_no_railway_imports_in_software_delivery_lane(self) -> None:
        sd_packages = [SD_ROOT, REPO_ROOT / "aethos_core" / "software_delivery" / "multi_agent"]
        for package in sd_packages:
            if not package.is_dir():
                continue
            for path in package.glob("*.py"):
                text = path.read_text(encoding="utf-8")
                assert "providers.railway" not in text, f"Railway import in {path.name}"
                assert "from aethos_core.providers.railway" not in text

    def test_deferred_work_after_freeze(self) -> None:
        assert any("executor" in item.lower() for item in SOFTWARE_DELIVERY_DEFERRED_AFTER_FREEZE)
        assert any("merge" in item.lower() or "parallel" in item.lower() for item in SOFTWARE_DELIVERY_DEFERRED_AFTER_FREEZE)

    def test_lane_docs_exist(self) -> None:
        for rel in SOFTWARE_DELIVERY_LANE_DOC_PATHS:
            assert (REPO_ROOT / rel).is_file(), f"missing doc: {rel}"

    def test_index_freeze_and_runbook_docs(self) -> None:
        index = REPO_ROOT / "docs/SOFTWARE_DELIVERY_PHASE_2_INDEX.md"
        freeze = REPO_ROOT / "docs/SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md"
        runbook = REPO_ROOT / "docs/SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md"
        assert index.is_file()
        assert freeze.is_file()
        assert runbook.is_file()
        index_text = index.read_text(encoding="utf-8")
        assert "Do not skip workflow stages" in index_text
        assert "infrastructure_mutation_lane" in index_text.replace(" ", "")

    def test_collect_only_meets_minimum_test_count(self) -> None:
        import os

        modules = _certify_modules_from_makefile()
        env = os.environ.copy()
        env["AETHOS_CERTIFICATION_MODE"] = "true"
        result = subprocess.run(
            ["python", "-m", "pytest", *modules, "--collect-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout + result.stderr)
        assert match is not None
        assert int(match.group(1)) >= SOFTWARE_DELIVERY_MIN_TEST_COUNT
