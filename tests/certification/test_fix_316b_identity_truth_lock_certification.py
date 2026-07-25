# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_316B_CERTIFICATION_REQUIREMENTS
from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    IDENTITY_TRUTH_LOCK_DOMAINS,
    IDENTITY_TRUTH_LOCK_FIX,
    IDENTITY_TRUTH_LOCK_ROUTE_ID,
    PLATFORM_CREATOR,
)
from aethos_core.identity_truth_lock.identity_truth_lock_service import build_identity_truth_lock

pytestmark = pytest.mark.certification


class TestFix316bIdentityTruthLockCertification:
    def test_fix_316b_contract(self) -> None:
        assert IDENTITY_TRUTH_LOCK_FIX == "FIX 316B"
        assert IDENTITY_TRUTH_LOCK_ROUTE_ID == "identity_truth_lock"
        assert len(IDENTITY_TRUTH_LOCK_DOMAINS) == 10

    def test_fix_316b_certification_requirement_count(self) -> None:
        assert len(FIX_316B_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_316b_creator_attribution_registry(self) -> None:
        sections = build_identity_truth_lock(session_id="cert-316b").sections
        creator = sections["creator_attribution_registry"]
        assert creator["creator"] == PLATFORM_CREATOR
        assert creator["questions"]["who_created_aethos"] == PLATFORM_CREATOR

    def test_fix_316b_validation_report(self) -> None:
        report = build_identity_truth_lock(session_id="cert-316b").sections["identity_truth_validation_report"]
        assert report["overall_ok"] is True
