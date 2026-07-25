# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F3 — multi-customer value proof program."""

from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_contract import (
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_service import (
    build_multi_customer_value_proof_program,
)

__all__ = [
    "MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID",
    "build_multi_customer_value_proof_program",
]
