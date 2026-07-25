# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 — customer value & adoption validation program."""

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_service import (
    build_customer_value_adoption_validation_program,
)

__all__ = [
    "CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID",
    "build_customer_value_adoption_validation_program",
]
