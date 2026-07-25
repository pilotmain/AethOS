# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A2 — Atlas Trader operational proof program."""

from aethos_core.workstreams.atlas_operational_proof_program.atlas_operational_proof_program_contract import (
    ATLAS_OPERATIONAL_PROOF_PROGRAM_ID,
    ATLAS_OPERATIONAL_PROOF_PROGRAM_PHASES,
)
from aethos_core.workstreams.atlas_operational_proof_program.atlas_operational_proof_program_service import (
    build_atlas_operational_proof_program,
)

__all__ = [
    "ATLAS_OPERATIONAL_PROOF_PROGRAM_ID",
    "ATLAS_OPERATIONAL_PROOF_PROGRAM_PHASES",
    "build_atlas_operational_proof_program",
]
