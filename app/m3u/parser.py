import json
import re
from urllib.parse import urljoin

import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def parse_m3u_content(content, base_url=None):
    """Parsea contenido M3U en una lista de canales.

    Ignora directivas intermedias y resuelve URLs relativas si se
    proporciona base_url. Extrae headers HTTP (User-Agent, Referer,
    Cookie) declarados en la entrada o en directivas #EXTVLCOPT/#EXTHTTP.
    """
    channels = []
    seen_urls = set()

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF"):
            continue

        url, directives = _find_stream(lines, i)
        if not url:
            continue

        if base_url:
            url = _resolve_url(base_url, url)

        if url in seen_urls:
            continue
        seen_urls.add(url)

        name = _parse_name(line)
        logo = _parse_attr(line, "tvg-logo")
        group_title = _parse_attr(line, "group-title")
        groups = [
            group.strip()
            for group in group_title.split(";")
            if group.strip()
        ]

        if not groups:
            groups = ["Sin categoría"]

        channels.append(
            {
                "id": _parse_attr(line, "tvg-id"),
                "name": name,
                "url": url,
                "logo": logo,
                "group": groups[0],
                "groups": groups,
                "headers": _parse_headers(line, directives),
            }
        )

    return channels


def _find_stream(lines, extinf_index):
    """Busca URL y directivas despues de #EXTINF.

    Devuelve (url, directivas). Si aparece otro #EXTINF antes de una URL
    la entrada actual no tiene stream y se ignora.
    """
    directives = []

    for i in range(extinf_index + 1, len(lines)):
        candidate = lines[i]

        if candidate.startswith("#EXTINF"):
            return None, directives

        if candidate.startswith(("#EXTVLCOPT:", "#EXTHTTP:")):
            directives.append(candidate)
            continue

        if candidate.startswith("#"):
            continue

        return candidate, directives

    return None, directives


def _parse_name(extinf_line):
    """Extrae el nombre del canal de la linea #EXTINF.

    Busca la primera coma fuera de comillas, porque atributos como
    http-user-agent pueden contener comas.
    """
    quote = None

    for index, char in enumerate(extinf_line):
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue

        if char == "," and quote is None:
            return extinf_line[index + 1:].strip()

    return "Canal desconocido"


def _parse_attr(line, attr):
    """Extrae un atributo de #EXTINF, soportando comillas simples y dobles."""
    match = re.search(
        rf"(?:^|\s){re.escape(attr)}=['\"]([^'\"]*)['\"]",
        line,
    )
    return match.group(1) if match else ""


def _parse_headers(extinf_line, directives):
    """Combina headers de atributos, #EXTVLCOPT y #EXTHTTP."""
    vlc_options = {}

    for directive in directives:
        if directive.upper().startswith("#EXTVLCOPT:"):
            option = directive.split(":", 1)[1]
            key, _, value = option.partition("=")

            if key and value:
                vlc_options[key.strip().lower()] = value.strip()

    headers = {}

    user_agent = _parse_attr(extinf_line, "http-user-agent")
    if not user_agent:
        user_agent = vlc_options.get("http-user-agent", "")

    if user_agent:
        headers["User-Agent"] = user_agent

    referrer = _parse_attr(extinf_line, "http-referrer")
    if not referrer:
        referrer = vlc_options.get("http-referrer", "")

    if referrer:
        headers["Referer"] = referrer

    for directive in directives:
        if not directive.upper().startswith("#EXTHTTP:"):
            continue

        headers.update(_parse_ext_http(directive.split(":", 1)[1]))

    return headers


def _parse_ext_http(raw):
    """Parsea #EXTHTTP:{"User-Agent": "...", "Referer": "..."}."""
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}

    if not isinstance(data, dict):
        return {}

    normalized = {}

    for key, value in data.items():
        if not isinstance(value, str):
            continue

        lowered = str(key).strip().lower()

        if lowered == "user-agent":
            normalized["User-Agent"] = value
        elif lowered in ("referer", "referrer"):
            normalized["Referer"] = value
        elif lowered == "cookie":
            normalized["Cookie"] = value

    return normalized


def _resolve_url(base_url, relative_url):
    """Resuelve una URL relativa contra la base."""
    if relative_url.startswith(("http://", "https://")):
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
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()

    return parse_m3u_content(response.text, base_url=url)
