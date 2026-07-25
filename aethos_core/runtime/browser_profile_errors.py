# SPDX-License-Identifier: Apache-2.0
"""Structured errors for browser profile persistence."""

from __future__ import annotations


class BrowserProfileSaveError(Exception):
    def __init__(self, code: str, detail: str, *, http_status: int = 409) -> None:
        self.code = code
        self.detail = detail
        self.http_status = http_status
        super().__init__(detail)

    def to_dict(self) -> dict[str, object]:
        return {"ok": False, "code": self.code, "detail": self.detail}
