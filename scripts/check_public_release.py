# SPDX-License-Identifier: Apache-2.0
"""Fail when repository content is inconsistent with a public OSS release."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    "README.md",
    "LICENSE",
    "NOTICE",
    "LICENSING.md",
    "COPYRIGHT.md",
    "CONTRIBUTING.md",
    "DCO.md",
    "GOVERNANCE.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CHANGELOG.md",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/workflows/dco.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/dependency-review.yml",
    ".github/workflows/installers.yml",
    "install.sh",
    "install.ps1",
    "run.sh",
    "run.ps1",
    "docs/INSTALL.md",
    "docs/README.md",
    "docs/OPEN_SOURCE_RELEASE.md",
}
ALLOWED_ROOT_MARKDOWN = REQUIRED_FILES | {
    "DISCLAIMER.md",
    "MEMORY.md",
    "SOUL.md",
    "COVERAGE_MATRIX.md",
}
PUBLIC_TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".lock",
    ".md",
    ".mjs",
    ".rst",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
PERSONAL_MARKERS = ("/Users/raya", "rayameha@gmail.com")
CONTRADICTORY_LICENSE_PHRASES = (
    "source-available and private",
    "private / all rights reserved",
    "commercial extensions available separately",
    "no public distribution license is granted",
)


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="surrogateescape").split("\0")[:-1]


def main() -> int:
    errors: list[str] = []
    paths = tracked_paths()
    existing = {name for name in paths if (ROOT / name).is_file()}
    # New policy files can be verified before they are staged locally. In CI,
    # checkout guarantees that every present repository file is tracked.
    existing.update(name for name in REQUIRED_FILES if (ROOT / name).is_file())

    for name in sorted(REQUIRED_FILES - existing):
        errors.append(f"required public-release file is missing: {name}")

    malformed = [name for name in existing if any(ord(char) < 32 for char in name)]
    for name in malformed:
        errors.append(f"tracked filename contains a control character: {name!r}")

    for name in sorted(existing):
        if name.startswith((".claude/", ".cursor/")):
            errors.append(f"private editor configuration is tracked: {name}")
        if "/" not in name and name.endswith(".md") and name not in ALLOWED_ROOT_MARKDOWN:
            errors.append(f"unapproved root-level Markdown file: {name}")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8").lower()
    if "apache license" not in license_text or "version 2.0, january 2004" not in license_text:
        errors.append("LICENSE is not the canonical Apache License 2.0 text")

    for name in sorted(existing):
        path = ROOT / name
        if path.suffix.lower() not in PUBLIC_TEXT_SUFFIXES:
            continue
        if name.startswith(("tests/", "web/__tests__/")):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in PERSONAL_MARKERS:
            if marker in text:
                errors.append(f"maintainer-specific value {marker!r} remains in {name}")
        for phrase in CONTRADICTORY_LICENSE_PHRASES:
            if phrase in text.lower():
                errors.append(f"contradictory license phrase {phrase!r} remains in {name}")

    for name in sorted(existing):
        path = ROOT / name
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".mjs", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        identifiers = re.findall(
            r"(?m)^(?:#|//)\s*SPDX-License-Identifier:\s*([A-Za-z0-9.-]+)\s*$",
            text,
        )
        for identifier in identifiers:
            if identifier != "Apache-2.0":
                errors.append(f"unexpected SPDX identifier {identifier!r} in {name}")

    if ".env" in existing:
        errors.append(".env is tracked; remove it and rotate any exposed credentials")
    if ".env.example" not in existing:
        errors.append(".env.example must be tracked")

    if errors:
        print("Public-release audit failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"Public-release audit passed ({len(existing)} tracked files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
