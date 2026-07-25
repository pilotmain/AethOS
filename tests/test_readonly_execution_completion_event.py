# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.job_artifacts import chat_completion_event_message


def test_readonly_execution_completion_bubble_is_short_and_specific():
    msg = chat_completion_event_message(
        "readonly_execution_vercel",
        "Read-only execution — list domains (invoicepilot)",
        "- old summary",
        fallback=False,
        operation_type="list_domains",
        target_name="invoicepilot",
        readonly_execution={
            "confidence": "confirmed",
            "data_source": "provider_api",
            "evidence": [
                {"type": "domain_record", "message": "invoicepilot.com"},
                {"type": "domain_record", "message": "invoicepilot.vercel.app"},
            ],
        },
    )
    assert "Read-only execution completed — list domains for `invoicepilot`" in msg
    assert "Found 2 domain record(s)" in msg
    assert "Provider API" in msg
    assert "Mission Control → Jobs → Read-only executions" in msg
    assert "# Read-only execution report" not in msg


def test_why_down_completion_includes_confidence():
    msg = chat_completion_event_message(
        "readonly_execution_vercel",
        "Read-only execution — why down (talking-avatar-agent)",
        "",
        fallback=False,
        operation_type="why_down",
        target_name="talking-avatar-agent",
        readonly_execution={
            "confidence": "confirmed",
            "probable_root_cause": "Build failed: missing NEXT_PUBLIC_API_URL",
            "data_source": "provider_api",
            "operational_events": [{"label": "deployment failed"}],
        },
    )
    assert "Failure confidence: confirmed" in msg
    assert "NEXT_PUBLIC_API_URL" in msg
    assert "Operational timeline: 1 event(s)" in msg
