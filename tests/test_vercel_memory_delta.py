# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.operational_memory import compute_vercel_memory_delta


def test_memory_delta_sections():
    delta = compute_vercel_memory_delta(
        ["invoicepilot", "quotepilot", "lifeos"],
        ["invoicepilot", "quotepilot", "wingman"],
    )
    assert delta["confirmed_this_run"] == ["invoicepilot", "quotepilot"]
    assert delta["newly_detected_this_run"] == ["lifeos"]
    assert delta["known_not_visible"] == ["wingman"]
