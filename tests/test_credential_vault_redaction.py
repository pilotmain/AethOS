# SPDX-License-Identifier: Apache-2.0

from aethos_core.security.secret_redaction import mask_secret, redact_text


def test_mask_secret_hides_middle():
    masked = mask_secret("vercel_abcdefghijklmnopqrstuvwxyz")
    assert "abcdefghijklmnopqrstuvwxyz" not in masked
    assert masked.startswith("verc")


def test_redact_text_masks_bearer_tokens():
    raw = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456"
    out = redact_text(raw)
    assert "abcdefghijklmnopqrstuvwxyz123456" not in out
