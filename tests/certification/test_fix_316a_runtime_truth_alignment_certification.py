# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — runtime truth alignment certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_316A_CERTIFICATION_REQUIREMENTS
from aethos_core.runtime_truth_alignment.governance_footer_policy import should_show_governance_footer
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_contract import (
    RUNTIME_CLASSIFICATION_DOMAINS,
    RUNTIME_TRUTH_ALIGNMENT_FIX,
    RUNTIME_TRUTH_ALIGNMENT_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix316aRuntimeTruthAlignmentCertification:
    def test_fix_316a_contract(self) -> None:
        assert RUNTIME_TRUTH_ALIGNMENT_FIX == "FIX 316A"
        assert RUNTIME_TRUTH_ALIGNMENT_ROUTE_ID == "runtime_truth_alignment"
        assert "platform_identity_response" in RUNTIME_CLASSIFICATION_DOMAINS
        assert "human_support_response" in RUNTIME_CLASSIFICATION_DOMAINS

    def test_fix_316a_certification_requirement_count(self) -> None:
        assert len(FIX_316A_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_316a_footer_policy(self) -> None:
        assert should_show_governance_footer(text="Who are you?", intent="platform_identity_response") is False
        assert should_show_governance_footer(text="Deploy api", intent="mutation_preflight") is True

    def test_fix_316a_classification_domains(self) -> None:
        assert classify_runtime_prompt("What can you do?") == "capability_response"
        assert classify_runtime_prompt("Who created you?") == "creator_attribution_response"
