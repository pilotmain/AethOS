# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 — governed strategic execution program."""

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_service import (
    build_governed_strategic_execution_program,
)

__all__ = [
    "GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID",
    "build_governed_strategic_execution_program",
]
