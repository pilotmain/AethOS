# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from aethos_core.operational_session.operational_readonly_goal import (
    classify_readonly_goal,
    is_operational_kernel_candidate,
)
from aethos_core.operational_session.operational_session import load_operational_session
from aethos_core.operational_session.session_subject import SessionSubject


def test_validate_vercel_connection_is_kernel_candidate():
    assert is_operational_kernel_candidate("validate vercel connection", session_id="val-1")


def test_classify_validate_vercel_connection():
    session = load_operational_session(session_id="val-2")
    goal = classify_readonly_goal(
        "validate vercel connection",
        subject=SessionSubject(provider="vercel"),
        session=session,
    )
    assert goal is not None
    assert goal.operation == "validate_connection"
