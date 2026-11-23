import json


class FavoritesStore:
    """Favoritos persistidos como canales completos.

    La clave estable es tvg-id cuando existe; si no, la URL. Un favorito
    guardado sigue disponible aunque la playlist actual no lo contenga.
    """

    SETTINGS_KEY = "favorites/channels"
    LEGACY_KEY = "favorites/urls"

    def __init__(self, settings):
        self.settings = settings
        self._items = {}
        self._load()

    def _load(self):
        raw = self.settings.value(self.SETTINGS_KEY, "", type=str)

        if raw:
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                data = []
        else:
            data = []

        if isinstance(data, dict):
            data = list(data.values())

        for channel in data or []:
            channel = self._normalize(channel)

            if channel is not None:
                self._items[self.key(channel)] = channel

        migrated = False

        for url in self.settings.value(self.LEGACY_KEY, [], type=list) or []:
            channel = self._normalize({"url": url, "name": url})

            if channel is None:
                continue

            key = self.key(channel)

            if key not in self._items:
                self._items[key] = channel
                migrated = True

        if migrated:
            self.save()

        if migrated or raw:
            self.settings.remove(self.LEGACY_KEY)

    def _normalize(self, channel):
        if not isinstance(channel, dict):
            return None

        url = channel.get("url")

        if not url:
            return None

        headers = channel.get("headers")

        return {
            "id": str(channel.get("id") or ""),
            "name": str(channel.get("name") or url),
            "url": str(url),
            "logo": str(channel.get("logo") or ""),
            "group": str(channel.get("group") or ""),
            "groups": [
                str(group)
                for group in (channel.get("groups") or [])
                if group
            ],
            "headers": dict(headers) if isinstance(headers, dict) else {},
        }

    def key(self, channel):
        return str(channel.get("id") or channel.get("url") or "")

    def is_favorite(self, channel):
        if channel is None:
            return False

        key = self.key(channel)

        if key and key in self._items:
            return True

        url = channel.get("url")
        return any(item["url"] == url for item in self._items.values())

    def toggle(self, channel):
        """Agrega o quita un canal. Devuelve True si quedo guardado."""
        if channel is None:
            return False

        normalized = self._normalize(channel)

        if normalized is None:
            return False

        key = self.key(normalized)
        existing_key = key if key in self._items else None

        if existing_key is None:
            for item_key, item in self._items.items():
                if item["url"] == normalized["url"]:
                    existing_key = item_key
                    break

        if existing_key is not None:
            del self._items[existing_key]
            added = False
        else:
            self._items[key] = normalized
            added = True

        self.save()

        return added

    def remove(self, channel):
        if channel is None:
            return

        key = self.key(channel)

        if key in self._items:
            del self._items[key]
            self.save()
            return

        url = channel.get("url")

        for item_key, item in list(self._items.items()):
            if item["url"] == url:
                del self._items[item_key]
                self.save()
                return

    def count(self):
        return len(self._items)

    def merge(self, channels):
        """Lista de favoritos, enriquecida con la playlist actual.

        Mantiene favoritos ausentes de la playlist y actualiza URL, logo,
        headers y nombre desde la version vigente cuando coincide.
        """
        by_key = {}
        by_url = {}

        for channel in channels:
            key = self.key(channel)

            if key:
                by_key[key] = channel

            url = channel.get("url")

            if url:
                by_url[url] = channel

        merged = []

        for key, saved in self._items.items():
            current = by_key.get(key) or by_url.get(saved["url"])

            if current is not None:
                merged.append(current)
            else:
                merged.append(saved)

        return merged

    def save(self):
        self.settings.setValue(
            self.SETTINGS_KEY,
            json.dumps(
                list(self._items.values()),
                ensure_ascii=False,
            ),
        )
        self.settings.sync()
