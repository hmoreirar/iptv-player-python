import pytest

pytest.importorskip("PySide6")

from app.m3u.iptv_org import (
    DEFAULT_PLAYLIST_URL,
    build_playlist_url,
    metadata_label,
    normalize_metadata,
)


class TestBuildPlaylistUrl:
    def test_default_playlist(self):
        assert DEFAULT_PLAYLIST_URL.endswith("/index.m3u")

    def test_country(self):
        assert (
            build_playlist_url("countries", "es")
            == "https://iptv-org.github.io/iptv/countries/es.m3u"
        )

    def test_category(self):
        assert (
            build_playlist_url("categories", "news")
            == "https://iptv-org.github.io/iptv/categories/news.m3u"
        )

    def test_language(self):
        assert (
            build_playlist_url("languages", "eng")
            == "https://iptv-org.github.io/iptv/languages/eng.m3u"
        )

    def test_unknown_kind(self):
        with pytest.raises(ValueError):
            build_playlist_url("regions", "afr")


class TestNormalizeMetadata:
    def test_countries(self):
        data = [
            {"name": "Spain", "code": "ES"},
            {"name": "Argentina", "code": "AR"},
        ]

        items = normalize_metadata("countries", data)

        assert [item["code"] for item in items] == ["AR", "ES"]
        assert items[0]["name"] == "Argentina"

    def test_categories(self):
        data = [
            {"id": "news", "name": "News"},
            {"id": "movies", "name": "Movies"},
        ]

        items = normalize_metadata("categories", data)

        assert [item["code"] for item in items] == ["movies", "news"]

    def test_languages(self):
        data = [
            {"name": "English", "code": "eng"},
            {"name": "Spanish", "code": "spa"},
        ]

        items = normalize_metadata("languages", data)

        assert [item["code"] for item in items] == ["eng", "spa"]

    def test_skips_incomplete_entries(self):
        data = [
            {"name": "Spain", "code": "ES"},
            {"name": "Missing code"},
            {"code": "XX"},
        ]

        items = normalize_metadata("countries", data)

        assert len(items) == 1

    def test_empty(self):
        assert normalize_metadata("countries", None) == []

    def test_label(self):
        label = metadata_label({"name": "Spain", "code": "ES"})

        assert label == "Spain (ES)"
