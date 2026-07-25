# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 — customer scale validation program."""

from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    CUSTOMER_SCALE_VALIDATION_PROGRAM_ID,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_service import (
    build_customer_scale_validation_program,
)

__all__ = [
    "CUSTOMER_SCALE_VALIDATION_PROGRAM_ID",
    "build_customer_scale_validation_program",
]
