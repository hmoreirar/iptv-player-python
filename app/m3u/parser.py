import re

import requests


def parse_m3u_content(content):
    channels = []

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF"):
            continue

        if i + 1 >= len(lines):
            continue

        stream_url = lines[i + 1]

        if "," in line:
            name = line.split(",", 1)[1].strip()
        else:
            name = "Canal desconocido"

        logo_match = re.search(r'tvg-logo="([^"]*)"', line)
        logo = logo_match.group(1) if logo_match else ""

        group_match = re.search(r'group-title="([^"]*)"', line)
        group = group_match.group(1) if group_match else "Sin categoría"

        channels.append(
            {
                "name": name,
                "url": stream_url,
                "logo": logo,
                "group": group,
            }
        )

    return channels


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
        timeout=30,
    )

    response.raise_for_status()

    return parse_m3u_content(response.text)
