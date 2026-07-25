# SPDX-License-Identifier: Apache-2.0

from aethos_core.research.comparison_html import comparison_html_public_url, persist_comparison_html


def test_comparison_html_public_url_uses_cdn_base(monkeypatch) -> None:
    monkeypatch.setenv("COMPARISON_HTML_PUBLIC_BASE_URL", "https://cdn.example.com")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    url = comparison_html_public_url("rrun-abc")
    assert url == "https://cdn.example.com/comparisons/comparison-rrun-abc.html"
    get_settings.cache_clear()


def test_comparison_html_public_url_api_fallback(monkeypatch) -> None:
    monkeypatch.setenv("COMPARISON_HTML_PUBLIC_BASE_URL", "")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    url = comparison_html_public_url("rrun-abc")
    assert url == "/api/v1/research/comparison-html/rrun-abc"
    get_settings.cache_clear()


def test_mirror_comparison_to_web_public(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("COMPARISON_HTML_MIRROR_WEB_PUBLIC", "true")
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    saved = persist_comparison_html(replay_id="rrun-mirror", html="<html>ok</html>")
    assert saved.get("web_public_path") == "/comparisons/comparison-rrun-mirror.html"
    public_file = tmp_path / "web" / "public" / "comparisons" / "comparison-rrun-mirror.html"
    assert public_file.is_file()
    get_settings.cache_clear()
