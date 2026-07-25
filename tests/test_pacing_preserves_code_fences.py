# SPDX-License-Identifier: Apache-2.0

from aethos_core.conversation.polish_compat import pace_response


def test_pace_response_preserves_fenced_html():
    body = (
        "Intro\n\n"
        "**Recommendation:** pick A\n\n"
        "Save file:\n\n"
        "```html\n<!DOCTYPE html><html><body>hello</body></html>\n```\n\n"
        "Replay: `rrun-abc`"
    )
    out = pace_response(body)
    assert "```html" in out
    assert "<!DOCTYPE html>" in out
