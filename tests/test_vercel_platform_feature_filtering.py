# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_navigation_map import (
    is_platform_feature_slug,
    is_plausible_project_name,
)


def test_platform_features_rejected():
    for slug in ("workflows", "blob-storage", "ai-gateway", "edge-config", "web-analytics"):
        assert is_platform_feature_slug(slug)
        assert not is_plausible_project_name(slug)


def test_real_apps_still_accepted():
    for name in ("invoicepilot", "quotepilot", "pilot-os-ui", "talking-avatar-agent"):
        assert is_plausible_project_name(name)
