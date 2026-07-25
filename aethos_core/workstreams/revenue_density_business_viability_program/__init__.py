# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G3 — revenue density & business viability program."""

from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_service import (
    build_revenue_density_business_viability_program,
)

__all__ = [
    "REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID",
    "build_revenue_density_business_viability_program",
]
