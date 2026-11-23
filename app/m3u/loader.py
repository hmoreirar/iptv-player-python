import requests
from PySide6.QtCore import QThread, Signal

from app.m3u import cache
from app.m3u.iptv_org import USER_AGENT
from app.m3u.parser import parse_m3u_content

CACHE_TTL_HOURS = 24


class PlaylistLoader(QThread):
    loaded = Signal(list)
    failed = Signal(str)
    warning = Signal(str)

    def __init__(self, source, is_url, force_refresh=False):
        super().__init__()
        self.source = source
        self.is_url = is_url
        self.force_refresh = force_refresh
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        try:
            if self._abort:
                return

            if self.is_url:
                content = self._load_url()
            else:
                content = self._load_file()
        except Exception as error:
            if not self._abort:
                self.failed.emit(str(error))
            return

        if self._abort:
            return

        channels = parse_m3u_content(
            content,
            base_url=self.source if self.is_url else None,
        )

        if not self._abort:
            self.loaded.emit(channels)

    def _load_file(self):
        with open(
            self.source,
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as file:
            return file.read()

    def _load_url(self):
        path = cache.cache_dir() / f"{cache.key_for(self.source)}.m3u"

        if not self.force_refresh and cache.is_fresh(path, CACHE_TTL_HOURS):
            content = cache.read_text(path)

            if content is not None:
                return content

        try:
            content = self._download()
        except Exception:
            cached = cache.read_text(path)

            if cached is not None:
                self.warning.emit(
                    "Sin conexion: usando una copia local de la playlist."
                )
                return cached

            raise

        cache.write_text(path, content)

        return content

    def _download(self):
        response = requests.get(
            self.source,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()

        return response.text
