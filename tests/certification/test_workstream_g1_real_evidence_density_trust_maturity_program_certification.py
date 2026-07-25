# SPDX-License-Identifier: Apache-2.0
"""FIX 354 / WORKSTREAM_G1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_354_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_354,
    AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_354,
    GOVERNANCE_MUTATION_FIX_354,
    LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_FIX,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_INVARIANT,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ROUTE_ID,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_SCHEMA_VERSION,
    TRUST_AUTHORITY_FIX_354,
    TRUST_MUTATION_AUTHORITY_FIX_354,
    TRUST_PROMOTION_FIX_354,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_service import (
    build_real_evidence_density_trust_maturity_program,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store import (
    clear_evidence_maturity_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-g1-cert-354"


@pytest.fixture(autouse=True)
def _clean():
    clear_evidence_maturity_records_for_tests()
    yield
    clear_evidence_maturity_records_for_tests()


class TestWorkstreamG1RealEvidenceDensityTrustMaturityCertification:
    def test_fix_354_contract(self) -> None:
        assert REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_FIX == "FIX 354"
        assert REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID == "WORKSTREAM_G1"
        assert REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_SCHEMA_VERSION == (
            "workstream_real_evidence_density_trust_maturity_program_v1"
        )
        assert TRUST_AUTHORITY_FIX_354 is False
        assert TRUST_PROMOTION_FIX_354 is False
        assert AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354 is False
        assert GOVERNANCE_MUTATION_FIX_354 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_354 is False
        assert AUTHORITY_EXPANSION_FIX_354 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_354 is False
        assert LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354 is True

    def test_fix_354_density_not_trust_authority(self) -> None:
        board = build_real_evidence_density_trust_maturity_program(
            session_id=SESSION
        ).real_evidence_density_trust_maturity_program
        assert set(board["fix_354_certification_requirements"]) == set(FIX_354_CERTIFICATION_REQUIREMENTS)
        assert board["trust_authority"] is False
        assert "trust_authority" in REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_INVARIANT

    def test_fix_354_phases_present(self) -> None:
        sections = build_real_evidence_density_trust_maturity_program(
            session_id=SESSION
        ).real_evidence_density_trust_maturity_program["sections"]
        for phase in REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES:
            assert sections[phase]

    def test_fix_354_certification_requirement_count(self) -> None:
        assert len(FIX_354_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_354_route_id(self) -> None:
        assert REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ROUTE_ID == (
            "workstream_real_evidence_density_trust_maturity_program"
        )
