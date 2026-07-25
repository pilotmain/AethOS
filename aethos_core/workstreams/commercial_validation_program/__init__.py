# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F5 — commercial validation program."""

from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_contract import (
    COMMERCIAL_VALIDATION_PROGRAM_ID,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_service import (
    build_commercial_validation_program,
)

__all__ = [
    "COMMERCIAL_VALIDATION_PROGRAM_ID",
    "build_commercial_validation_program",
]
