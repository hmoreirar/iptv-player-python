import hashlib
import json
import time
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def cache_dir():
    """Directorio de cache para playlists y metadatos."""
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.CacheLocation
    )

    if not base:
        base = str(Path.home() / ".cache" / "iptv-player")

    path = Path(base) / "playlists"
    path.mkdir(parents=True, exist_ok=True)

    return path


def key_for(value):
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def is_fresh(path, ttl_hours):
    try:
        age = time.time() - Path(path).stat().st_mtime
    except OSError:
        return False

    return age < ttl_hours * 3600


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def write_text(path, content):
    try:
        Path(path).write_text(content, encoding="utf-8")
    except OSError:
        pass


def read_json(path):
    content = read_text(path)

    if content is None:
        return None

    try:
        return json.loads(content)
    except (ValueError, TypeError):
        return None


def write_json(path, data):
    try:
        Path(path).write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass
