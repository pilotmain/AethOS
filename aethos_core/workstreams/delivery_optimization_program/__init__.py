# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C2 — delivery optimization program."""

from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    DELIVERY_OPTIMIZATION_PROGRAM_ID,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_service import (
    build_delivery_optimization_program,
)

__all__ = [
    "DELIVERY_OPTIMIZATION_PROGRAM_ID",
    "build_delivery_optimization_program",
]
