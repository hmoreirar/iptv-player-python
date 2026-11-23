from PySide6.QtCore import QSettings

from app.favorites import FavoritesStore


def make_store(tmp_path):
    settings = QSettings(str(tmp_path / "favorites.ini"), QSettings.IniFormat)
    return FavoritesStore(settings), settings


def channel(**overrides):
    data = {
        "id": "Canal.test@SD",
        "name": "Canal Test",
        "url": "http://example.com/canal.m3u8",
        "logo": "http://example.com/logo.png",
        "group": "News",
        "headers": {"User-Agent": "Test"},
    }
    data.update(overrides)
    return data


class TestFavoritesStore:
    def test_add_and_remove(self, tmp_path):
        store, _ = make_store(tmp_path)
        item = channel()

        assert store.toggle(item) is True
        assert store.is_favorite(item)
        assert store.count() == 1

        assert store.toggle(item) is False
        assert not store.is_favorite(item)
        assert store.count() == 0

    def test_persists_full_channel(self, tmp_path):
        store, settings = make_store(tmp_path)
        store.toggle(channel())

        reloaded = FavoritesStore(settings)
        item = channel()

        assert reloaded.is_favorite(item)
        assert reloaded.count() == 1

        merged = reloaded.merge([item])
        assert merged[0]["headers"]["User-Agent"] == "Test"

    def test_merge_keeps_favorites_outside_playlist(self, tmp_path):
        store, _ = make_store(tmp_path)
        store.toggle(channel())

        merged = store.merge([])

        assert len(merged) == 1
        assert merged[0]["url"] == "http://example.com/canal.m3u8"

    def test_merge_prefers_current_channel(self, tmp_path):
        store, _ = make_store(tmp_path)
        store.toggle(channel())

        current = channel(url="http://example.com/new-url.m3u8")
        merged = store.merge([current])

        assert merged[0]["url"] == "http://example.com/new-url.m3u8"

    def test_migrates_legacy_urls(self, tmp_path):
        settings = QSettings(str(tmp_path / "legacy.ini"), QSettings.IniFormat)
        settings.setValue("favorites/urls", ["http://example.com/old.m3u8"])
        settings.sync()

        store = FavoritesStore(settings)
        current = channel(
            id="",
            url="http://example.com/old.m3u8",
            name="Old Channel",
        )

        assert store.is_favorite(current)
        assert store.merge([current])[0]["name"] == "Old Channel"

    def test_toggle_removes_legacy_entry_with_url_match(self, tmp_path):
        settings = QSettings(str(tmp_path / "legacy2.ini"), QSettings.IniFormat)
        settings.setValue("favorites/urls", ["http://example.com/old.m3u8"])
        settings.sync()

        store = FavoritesStore(settings)
        current = channel(url="http://example.com/old.m3u8")

        assert store.toggle(current) is False
        assert store.count() == 0

    def test_missing_url_is_ignored(self, tmp_path):
        store, _ = make_store(tmp_path)

        assert store.toggle({"name": "Sin URL"}) is False
        assert store.count() == 0
