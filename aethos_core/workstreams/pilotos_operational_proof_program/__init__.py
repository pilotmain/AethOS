# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A1 — PilotOS UI operational proof program."""

from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_contract import (
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID,
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES,
)
from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_service import (
    build_pilotos_operational_proof_program,
)

__all__ = [
    "PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID",
    "PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES",
    "build_pilotos_operational_proof_program",
]
