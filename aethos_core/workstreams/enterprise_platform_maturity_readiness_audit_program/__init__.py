# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G4 — enterprise platform maturity & readiness audit."""

from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_contract import (
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_service import (
    build_enterprise_platform_maturity_readiness_audit_program,
)

__all__ = [
    "ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID",
    "build_enterprise_platform_maturity_readiness_audit_program",
]
