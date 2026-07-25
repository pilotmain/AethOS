# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_detail_inspector import (
    project_deployments_url,
    project_detail_url,
)


def test_detail_urls_are_observational_paths():
    assert project_detail_url("acme-team", "invoicepilot") == (
        "https://vercel.com/acme-team/invoicepilot"
    )
    assert project_deployments_url("acme-team", "invoicepilot").endswith("/deployments")
