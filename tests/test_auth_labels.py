# SPDX-License-Identifier: Apache-2.0

from aethos_core.connections.auth_labels import auth_method_label, auth_method_label_for_provider


def test_auth_method_label_for_provider_does_not_import_adapters():
    assert auth_method_label_for_provider("railway", "api_token") == "Railway API token"
    assert auth_method_label_for_provider("github", "api_token") == "GitHub API token"
    assert auth_method_label_for_provider("vercel", "api_token") == "Vercel API token"
    assert auth_method_label("browser") == "Saved browser session"
