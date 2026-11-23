#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
ICON_SRC="$ROOT/app/ui/assets/iptv-player.svg"

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS="$DATA_HOME/applications"
ICONS="$DATA_HOME/icons/hicolor/scalable/apps"

if [[ ! -x "$PYTHON" ]]; then
    echo "No existe el entorno virtual: $PYTHON" >&2
    echo "Crea el venv e instala requirements.txt primero." >&2
    exit 1
fi

if [[ ! -f "$ICON_SRC" ]]; then
    echo "Falta el icono: $ICON_SRC" >&2
    exit 1
fi

mkdir -p "$APPS" "$ICONS"

install -m 644 "$ICON_SRC" "$ICONS/iptv-player.svg"

cat > "$APPS/iptv-player.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=IPTV Player
GenericName=Reproductor IPTV
Comment=Reproductor de canales IPTV con modo TV
Exec="$PYTHON" -m app.main
Path=$ROOT
Icon=iptv-player
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=iptv;tv;m3u;player;
StartupNotify=true
StartupWMClass=iptv-player
EOF

chmod 644 "$APPS/iptv-player.desktop"

update-desktop-database "$APPS" >/dev/null 2>&1 || true
gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

echo "Lanzador instalado:"
echo "  $APPS/iptv-player.desktop"
echo "  $ICONS/iptv-player.svg"
