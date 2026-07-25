# SPDX-License-Identifier: Apache-2.0
"""FIX 347 / WORKSTREAM_F1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_347_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    AUTHORITY_EXPANSION_FIX_347,
    CUSTOMER_AUTHORITY_FIX_347,
    FIRST_CUSTOMER_DELIVERY_PILOT_PHASES,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_FIX,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_INVARIANT,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ROUTE_ID,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_347,
    LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347,
    TRUST_MUTATION_AUTHORITY_FIX_347,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_service import (
    build_first_customer_delivery_pilot_program,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    clear_first_customer_delivery_pilot_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f1-cert-347"


@pytest.fixture(autouse=True)
def _clean():
    clear_first_customer_delivery_pilot_records_for_tests()
    yield
    clear_first_customer_delivery_pilot_records_for_tests()


class TestWorkstreamF1FirstCustomerDeliveryPilotCertification:
    def test_fix_347_contract(self) -> None:
        assert FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_FIX == "FIX 347"
        assert FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID == "WORKSTREAM_F1"
        assert FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_SCHEMA_VERSION == (
            "workstream_first_customer_delivery_pilot_program_v1"
        )
        assert CUSTOMER_AUTHORITY_FIX_347 is False
        assert AUTHORITY_EXPANSION_FIX_347 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_347 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_347 is False
        assert LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347 is True

    def test_fix_347_pilot_not_customer_authority(self) -> None:
        board = build_first_customer_delivery_pilot_program(
            session_id=SESSION
        ).first_customer_delivery_pilot_program
        assert set(board["fix_347_certification_requirements"]) == set(FIX_347_CERTIFICATION_REQUIREMENTS)
        assert board["customer_authority"] is False
        assert "customer_authority" in FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_INVARIANT

    def test_fix_347_phases_present(self) -> None:
        sections = build_first_customer_delivery_pilot_program(
            session_id=SESSION
        ).first_customer_delivery_pilot_program["sections"]
        for phase in FIRST_CUSTOMER_DELIVERY_PILOT_PHASES:
            assert sections[phase]

    def test_fix_347_certification_requirement_count(self) -> None:
        assert len(FIX_347_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_347_route_id(self) -> None:
        assert FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ROUTE_ID == (
            "workstream_first_customer_delivery_pilot_program"
        )
