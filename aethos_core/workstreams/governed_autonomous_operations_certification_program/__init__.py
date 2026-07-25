# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 — governed autonomous operations certification program."""

from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_service import (
    build_governed_autonomous_operations_certification_program,
)

__all__ = [
    "GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID",
    "build_governed_autonomous_operations_certification_program",
]
