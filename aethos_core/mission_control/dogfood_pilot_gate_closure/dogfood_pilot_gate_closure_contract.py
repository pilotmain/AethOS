# SPDX-License-Identifier: Apache-2.0
"""FIX 181–186 — dogfood pilot manual gate closure contract (compose-only)."""

from __future__ import annotations

from typing import Final

DOGFOOD_PILOT_GATE_CLOSURE_SCHEMA_VERSION: Final[str] = "mission_control_dogfood_pilot_gate_closure_v1"
DOGFOOD_PILOT_GATE_CLOSURE_FIX: Final[str] = "FIX 181–186"
DOGFOOD_PILOT_GATE_CLOSURE_ROUTE_ID: Final[str] = "mission_control_dogfood_pilot_gate_closure"
DOGFOOD_PILOT_GATE_CLOSURE_ORIGIN: Final[str] = "mission_control_dogfood_pilot_gate_closure"

DOGFOOD_PILOT_GATE_CLOSURE_INVARIANT: Final[str] = (
    "dogfood_pilot_gate_closure_composes_fix_182_181_185_184_183_186_readiness_without_pilot_reexecution_or_governance_authority"
)

GATE_FIX_ORDER: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 182", "Repo pilot readiness dashboard"),
    ("FIX 181", "End-to-end repo development pilot harness"),
    ("FIX 185", "Issue intake scope fidelity"),
    ("FIX 184", "Issue intent alignment"),
    ("FIX 183", "Pilot validation trust board"),
    ("FIX 186", "Dogfood pilot trust report freeze"),
)

MIN_SCOPE_FIDELITY_SCORE_FIX_185: Final[int] = 80

DOGFOOD_PILOT_GATE_CLOSURE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("compose_only", "Gate closure composes upstream FIX layers — never re-runs pilots."),
    ("evidence_driven", "Each gate reflects persisted operational evidence, not architectural claims."),
    ("manual_signoff", "Operator review records remain required for FIX 186 before multi-repo expansion."),
    ("no_inherited_trust", "Gate closure for AethOS does not grant trust on other repositories."),
)
