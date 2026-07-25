# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_url_classifier import classify_url_type


def test_preview_team_url():
    assert (
        classify_url_type(
            "https://invoicepilot-nnusvd68a-rayameresas-projects.vercel.app"
        )
        == "preview_vercel"
    )


def test_production_vercel_subdomain():
    assert classify_url_type("https://pilot-os-ui.vercel.app") == "production_vercel"


def test_custom_domain():
    assert classify_url_type("https://useinvoicepilot.com") == "custom_domain"
