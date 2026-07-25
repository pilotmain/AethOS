# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 — real world delivery proof program."""

from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_service import (
    build_real_world_delivery_proof_program,
)

__all__ = [
    "REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID",
    "build_real_world_delivery_proof_program",
]
