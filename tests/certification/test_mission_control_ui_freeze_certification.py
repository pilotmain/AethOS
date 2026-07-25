# SPDX-License-Identifier: Apache-2.0
"""FIX 135 — Mission Control operator console UI freeze certification."""

from __future__ import annotations

from pathlib import Path

import pytest

from aethos_core.mission_control.approval_inbox.action_safety_review import review_mission_control_ui_action_safety
from aethos_core.mission_control.mission_control_ui_freeze_contract import (
    ALLOWED_MC_OPERATOR_HTTP_ROUTES,
    ALLOWED_UI_APPROVAL_GATE_IDS,
    FORBIDDEN_MC_OPERATOR_CAPABILITIES,
    FORBIDDEN_PROVIDER_SYMBOLS,
    FROZEN_OPERATOR_CONSOLE_VIEWS,
    FROZEN_UI_COMPONENT_PATHS,
    MISSION_CONTROL_SHIPPED_FIXES,
    MISSION_CONTROL_UI_DOC_PATHS,
    MISSION_CONTROL_UI_FREEZE_FIX,
    MISSION_CONTROL_UI_FROZEN,
    MISSION_CONTROL_UI_INVARIANT,
    MISSION_CONTROL_UI_ROUTE_MATRIX,
    UI_APPROVAL_CHAT_ENTRYPOINT,
    VIEW_ONLY_INBOX_GATE_IDS,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import (
    review_frozen_ui_components,
    review_frozen_web_api_clients,
    review_mission_control_operator_api_surface,
    review_mission_control_ui_freeze,
)

pytestmark = pytest.mark.certification

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestMissionControlUiFreezeCertification:
    def test_fix_135_contract_identity(self) -> None:
        assert MISSION_CONTROL_UI_FREEZE_FIX == "FIX 135"
        assert MISSION_CONTROL_UI_FROZEN is True
        assert "FIX 135" in MISSION_CONTROL_SHIPPED_FIXES
        assert "FIX 136" in MISSION_CONTROL_SHIPPED_FIXES
        assert "FIX 137" in MISSION_CONTROL_SHIPPED_FIXES
        assert "FIX 137B" in MISSION_CONTROL_SHIPPED_FIXES
        assert "resolve_chat_turn" in MISSION_CONTROL_UI_INVARIANT

    def test_frozen_operator_console_views(self) -> None:
        assert FROZEN_OPERATOR_CONSOLE_VIEWS == (
            "cross-lane-operations",
            "approval-inbox",
            "mission-job-replay",
        )

    def test_ui_eligible_vs_view_only_gates_disjoint(self) -> None:
        eligible = set(ALLOWED_UI_APPROVAL_GATE_IDS)
        view_only = set(VIEW_ONLY_INBOX_GATE_IDS)
        assert not eligible.intersection(view_only)

    def test_route_matrix_covers_frozen_views(self) -> None:
        matrix_views = {row["view_id"] for row in MISSION_CONTROL_UI_ROUTE_MATRIX}
        for view in FROZEN_OPERATOR_CONSOLE_VIEWS:
            assert view in matrix_views

    def test_frozen_docs_present(self) -> None:
        for rel in MISSION_CONTROL_UI_DOC_PATHS:
            assert (REPO_ROOT / rel).is_file(), rel

    def test_frozen_ui_components_exist_without_forbidden_buttons(self) -> None:
        for rel in FROZEN_UI_COMPONENT_PATHS:
            assert (REPO_ROOT / rel).is_file(), rel
        review = review_frozen_ui_components()
        assert review["ok"] is True, review.get("violations")

    def test_frozen_web_clients_readonly_except_governed_execute(self) -> None:
        review = review_frozen_web_api_clients()
        assert review["ok"] is True, review.get("violations")

    def test_operator_api_surface_frozen(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True, review.get("violations")
        assert len(review["routes"]) == len(ALLOWED_MC_OPERATOR_HTTP_ROUTES)

    def test_no_direct_provider_mutation_symbols_in_ui_path(self) -> None:
        safety = review_mission_control_ui_action_safety()
        assert safety["ok"] is True
        assert safety["chat_governance_entrypoint"] == UI_APPROVAL_CHAT_ENTRYPOINT
        for sym in FORBIDDEN_PROVIDER_SYMBOLS:
            assert sym not in safety.get("execution_path_violations", [])
            assert sym not in safety.get("api_route_violations", [])

    def test_forbidden_operator_capabilities_documented(self) -> None:
        assert "deploy" in FORBIDDEN_MC_OPERATOR_CAPABILITIES
        assert "merge" in FORBIDDEN_MC_OPERATOR_CAPABILITIES
        assert "provider_mutation_bypass" in FORBIDDEN_MC_OPERATOR_CAPABILITIES

    def test_aggregate_freeze_review_passes(self) -> None:
        review = review_mission_control_ui_freeze()
        assert review["ok"] is True
        assert review["fix"] == "FIX 135"
