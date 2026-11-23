from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.ui.theme import Colors

_SVG = {
    "play": '<path d="M8 5.5v13l10-6.5z" fill="{color}"/>',
    "pause": (
        '<rect x="7" y="5" width="3.5" height="14" rx="1" fill="{color}"/>'
        '<rect x="13.5" y="5" width="3.5" height="14" rx="1" fill="{color}"/>'
    ),
    "volume": (
        '<path d="M4 9.5h3.5L12 6v12l-4.5-3.5H4z" fill="none" '
        'stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>'
        '<path d="M15.5 9a4 4 0 010 6M18 6.5a7.5 7.5 0 010 11" '
        'fill="none" stroke="{color}" stroke-width="1.8" '
        'stroke-linecap="round"/>'
    ),
    "volume_off": (
        '<path d="M4 9.5h3.5L12 6v12l-4.5-3.5H4z" fill="none" '
        'stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>'
        '<path d="M16 9l5 6M21 9l-5 6" fill="none" stroke="{color}" '
        'stroke-width="1.8" stroke-linecap="round"/>'
    ),
    "fullscreen": (
        '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" fill="none" '
        'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
    ),
    "fullscreen_exit": (
        '<path d="M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5" fill="none" '
        'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
    ),
    "star": (
        '<path d="M12 3.6l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 '
        '1-5.8-4.3-4.1 5.9-.9z" fill="none" stroke="{color}" '
        'stroke-width="1.6" stroke-linejoin="round"/>'
    ),
    "star_filled": (
        '<path d="M12 3.6l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 '
        '1-5.8-4.3-4.1 5.9-.9z" fill="{color}" stroke="{color}" '
        'stroke-width="1.4" stroke-linejoin="round"/>'
    ),
    "search": (
        '<circle cx="10.5" cy="10.5" r="6" fill="none" stroke="{color}" '
        'stroke-width="1.8"/><path d="M15 15l4.5 4.5" fill="none" '
        'stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>'
    ),
    "refresh": (
        '<path d="M19 12a7 7 0 11-2.1-5M19 5v4.5h-4.5" fill="none" '
        'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
    ),
    "tv": (
        '<rect x="3.5" y="7" width="17" height="12" rx="2" fill="none" '
        'stroke="{color}" stroke-width="1.7"/>'
        '<path d="M8 3.5l4 3.5 4-3.5" fill="none" stroke="{color}" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    "history": (
        '<circle cx="12" cy="12" r="8" fill="none" stroke="{color}" '
        'stroke-width="1.7"/><path d="M12 7.5V12l3 2" fill="none" '
        'stroke="{color}" stroke-width="1.7" stroke-linecap="round"/>'
    ),
    "grid": (
        '<rect x="4" y="4" width="6.5" height="6.5" rx="1" fill="none" '
        'stroke="{color}" stroke-width="1.7"/>'
        '<rect x="13.5" y="4" width="6.5" height="6.5" rx="1" fill="none" '
        'stroke="{color}" stroke-width="1.7"/>'
        '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1" fill="none" '
        'stroke="{color}" stroke-width="1.7"/>'
        '<rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1" fill="none" '
        'stroke="{color}" stroke-width="1.7"/>'
    ),
    "folder": (
        '<path d="M3.5 7.5A1.5 1.5 0 015 6h4l2 2h8a1.5 1.5 0 011.5 1.5v8A1.5 '
        '1.5 0 0119 19H5a1.5 1.5 0 01-1.5-1.5z" fill="none" '
        'stroke="{color}" stroke-width="1.6" stroke-linejoin="round"/>'
    ),
    "link": (
        '<path d="M10 14l4-4M8.5 16.5l-1 1a3.5 3.5 0 01-5-5l3-3a3.5 3.5 0 '
        '015 0M15.5 7.5l1-1a3.5 3.5 0 015 5l-3 3a3.5 3.5 0 01-5 0" '
        'fill="none" stroke="{color}" stroke-width="1.7" '
        'stroke-linecap="round"/>'
    ),
    "chevron_down": (
        '<path d="M6 9l6 6 6-6" fill="none" stroke="{color}" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    "x": (
        '<path d="M6 6l12 12M18 6L6 18" fill="none" stroke="{color}" '
        'stroke-width="1.8" stroke-linecap="round"/>'
    ),
    "more": (
        '<circle cx="5" cy="12" r="1.6" fill="{color}"/>'
        '<circle cx="12" cy="12" r="1.6" fill="{color}"/>'
        '<circle cx="19" cy="12" r="1.6" fill="{color}"/>'
    ),
}

_cache = {}


def icon(name, color=None, size=18):
    color = color or Colors.text
    key = (name, color, size)

    if key in _cache:
        return _cache[key]

    body = _SVG.get(name)

    if body is None:
        raise KeyError(f"Icono desconocido: {name}")

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="24" height="24">{body.format(color=color)}</svg>'
    )

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(QSize(size * 2, size * 2))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)

    result = QIcon(pixmap)
    _cache[key] = result

    return result
