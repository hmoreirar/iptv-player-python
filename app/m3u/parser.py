import re
from urllib.parse import urljoin

import requests


def parse_m3u_content(content, base_url=None):
    """Parsea contenido M3U en una lista de canales.

    Ignora directivas intermedias (#EXTVLCOPT, #EXTGRP, etc.) y resuelve
    URLs relativas si se proporciona base_url.
    """
    channels = []
    seen_urls = set()

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF"):
            continue

        url = _find_stream_url(lines, i)
        if not url:
            continue

        if base_url:
            url = _resolve_url(base_url, url)

        if url in seen_urls:
            continue
        seen_urls.add(url)

        name = _parse_name(line)
        logo = _parse_attr(line, "tvg-logo")
        group = _parse_attr(line, "group-title") or "Sin categoría"

        channels.append(
            {
                "name": name,
                "url": url,
                "logo": logo,
                "group": group,
            }
        )

    return channels


def _find_stream_url(lines, extinf_index):
    """Busca la siguiente línea que sea una URL de stream después de #EXTINF.

    Si encuentra otro #EXTINF antes de una URL, la entrada actual no tiene
    stream y se ignora. Las directivas intermedias (#EXTVLCOPT, etc.) se saltan.
    """
    for i in range(extinf_index + 1, len(lines)):
        candidate = lines[i]

        if candidate.startswith("#EXTINF"):
            return None

        if candidate.startswith("#"):
            continue

        return candidate

    return None


def _parse_name(extinf_line):
    """Extrae el nombre del canal de la línea #EXTINF."""
    if "," in extinf_line:
        return extinf_line.split(",", 1)[1].strip()

    return "Canal desconocido"


def _parse_attr(line, attr):
    """Extrae un atributo de la línea #EXTINF, soportando comillas simples y dobles."""
    match = re.search(rf"{attr}=['\"]([^'\"]*)['\"]", line)
    return match.group(1) if match else ""


def _resolve_url(base_url, relative_url):
    """Resuelve una URL relativa contra la base."""
    if relative_url.startswith("http://") or relative_url.startswith("https://"):
        return relative_url

    return urljoin(base_url, relative_url)


def parse_m3u_file(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:
        content = file.read()

    return parse_m3u_content(content)


def parse_m3u_url(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return parse_m3u_content(response.text, base_url=url)
