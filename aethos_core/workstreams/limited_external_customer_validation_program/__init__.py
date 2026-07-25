# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_B1 — limited external customer validation program."""

from aethos_core.workstreams.limited_external_customer_validation_program.limited_external_customer_validation_program_contract import (
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID,
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES,
)
from aethos_core.workstreams.limited_external_customer_validation_program.limited_external_customer_validation_program_service import (
    build_limited_external_customer_validation_program,
)

__all__ = [
    "LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID",
    "LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES",
    "build_limited_external_customer_validation_program",
]
