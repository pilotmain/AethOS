# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F7 — business operating model validation program."""

from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_contract import (
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_service import (
    build_business_operating_model_validation_program,
)

__all__ = [
    "BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID",
    "build_business_operating_model_validation_program",
]
