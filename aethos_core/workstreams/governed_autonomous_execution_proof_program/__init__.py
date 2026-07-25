# SPDX-License-Identifier: Apache-2.0
"""PHASE_I2 — governed autonomous execution proof program."""

from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_contract import (
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_service import (
    build_governed_autonomous_execution_proof_program,
)

__all__ = [
    "GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID",
    "build_governed_autonomous_execution_proof_program",
]
