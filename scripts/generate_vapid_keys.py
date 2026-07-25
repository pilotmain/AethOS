#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate VAPID keypair for WEB_PUSH — paste into .env / Railway."""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid


def generate_vapid_keypair() -> tuple[str, str]:
    vapid = Vapid()
    vapid.generate_keys()
    private_pem = vapid.private_pem()
    if isinstance(private_pem, bytes):
        private_pem = private_pem.decode()
    raw = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    public_b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return public_b64, private_pem


def main() -> None:
    public_b64, private_pem = generate_vapid_keypair()
    print("VAPID_PUBLIC_KEY=" + public_b64)
    print("VAPID_PRIVATE_KEY=" + private_pem.replace("\n", "\\n"))
    print("VAPID_SUBJECT=mailto:ops@example.com")


if __name__ == "__main__":
    main()
