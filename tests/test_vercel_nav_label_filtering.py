# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel import (
    is_nav_label,
    is_plausible_project_name,
    is_platform_feature_slug,
)
from aethos_core.browser.platforms.vercel.vercel_navigation_map import KNOWN_VERCEL_NAV_LABELS


def test_known_nav_labels_rejected():
    for label in ("Hobby", "Deployments", "Analytics", "Upgrade", "Settings"):
        assert is_nav_label(label)
        assert not is_plausible_project_name(label)


def test_real_project_names_accepted():
    for name in ("invoicepilot", "lifeos", "pilot-os-ui", "talking-avatar-agent"):
        assert is_plausible_project_name(name)
        assert name not in KNOWN_VERCEL_NAV_LABELS


def test_mixed_case_nav_still_filtered():
    assert is_nav_label("OBSERVABILITY")
    assert not is_plausible_project_name("Firewall")
