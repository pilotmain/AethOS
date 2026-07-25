# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 — multi-cloud operational proof program."""

from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_service import (
    build_multi_cloud_operational_proof_program,
)

__all__ = [
    "MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID",
    "build_multi_cloud_operational_proof_program",
]
