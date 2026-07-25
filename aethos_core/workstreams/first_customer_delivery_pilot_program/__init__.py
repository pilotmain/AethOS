# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 — first customer delivery pilot program."""

from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_service import (
    build_first_customer_delivery_pilot_program,
)

__all__ = [
    "FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID",
    "build_first_customer_delivery_pilot_program",
]
