# SPDX-License-Identifier: Apache-2.0

import logging

from aethos_core.security.secret_redaction import safe_log_message


def test_no_secret_in_logs(caplog):
    token = "vercel_test_token_abcdefghijklmnopqrstuvwxyz"
    with caplog.at_level(logging.ERROR):
        logging.error("failed auth token=%s", safe_log_message(token))
    assert token not in caplog.text
    assert "verc" in caplog.text or "*" in caplog.text
