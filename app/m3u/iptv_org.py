"""Utilidades para las playlists publicas de iptv-org/iptv."""

import requests
from PySide6.QtCore import QThread, Signal

from app.m3u import cache

BASE_URL = "https://iptv-org.github.io/iptv"
API_URL = "https://iptv-org.github.io/api"

DEFAULT_PLAYLIST_URL = f"{BASE_URL}/index.m3u"

PLAYLIST_PATHS = {
    "countries": "countries",
    "categories": "categories",
    "languages": "languages",
}

METADATA_URLS = {
    "countries": f"{API_URL}/countries.json",
    "categories": f"{API_URL}/categories.json",
    "languages": f"{API_URL}/languages.json",
}

METADATA_TTL_HOURS = 24 * 7

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def build_playlist_url(kind, code):
    if kind not in PLAYLIST_PATHS:
        raise ValueError(f"Tipo de playlist desconocido: {kind}")

    return f"{BASE_URL}/{PLAYLIST_PATHS[kind]}/{code}.m3u"


def normalize_metadata(kind, data):
    """Convierte la respuesta de la API en una lista {code, name}."""
    items = []

    for entry in data or []:
        if kind == "countries":
            code = entry.get("code")
            name = entry.get("name")
        elif kind == "categories":
            code = entry.get("id")
            name = entry.get("name") or code
        elif kind == "languages":
            code = entry.get("code")
            name = entry.get("name") or code
        else:
            continue

        if not code or not name:
            continue

        items.append({"code": code, "name": name})

    items.sort(key=lambda item: item["name"].lower())

    return items


def fetch_metadata(kind, force=False):
    if kind not in METADATA_URLS:
        raise ValueError(f"Tipo de metadatos desconocido: {kind}")

    path = cache.cache_dir() / f"metadata-{kind}.json"

    if not force and cache.is_fresh(path, METADATA_TTL_HOURS):
        cached = cache.read_json(path)

        if cached:
            return normalize_metadata(kind, cached)

    response = requests.get(
        METADATA_URLS[kind],
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    cache.write_json(path, data)

    return normalize_metadata(kind, data)


def metadata_label(item):
    return f"{item['name']} ({item['code']})"


class MetadataWorker(QThread):
    loaded = Signal(str, list)
    failed = Signal(str, str)

    def __init__(self, kind, force=False):
        super().__init__()
        self.kind = kind
        self.force = force

    def run(self):
        try:
            items = fetch_metadata(self.kind, force=self.force)
        except Exception as error:
            self.failed.emit(self.kind, str(error))
            return

        self.loaded.emit(self.kind, items)
