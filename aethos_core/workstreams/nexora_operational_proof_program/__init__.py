# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A3 — Nexora operational proof program."""

from aethos_core.workstreams.nexora_operational_proof_program.nexora_operational_proof_program_contract import (
    NEXORA_OPERATIONAL_PROOF_PROGRAM_ID,
    NEXORA_OPERATIONAL_PROOF_PROGRAM_PHASES,
)
from aethos_core.workstreams.nexora_operational_proof_program.nexora_operational_proof_program_service import (
    build_nexora_operational_proof_program,
)

__all__ = [
    "NEXORA_OPERATIONAL_PROOF_PROGRAM_ID",
    "NEXORA_OPERATIONAL_PROOF_PROGRAM_PHASES",
    "build_nexora_operational_proof_program",
]
