#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${VERSION:-1.0.0}"
ARCH="${ARCH:-x86_64}"
APPDIR="$ROOT/dist-appimage/AppDir"
TOOLS="$ROOT/.tools"
APPIMAGE="$ROOT/dist/IPTV-Player-${VERSION}-${ARCH}.AppImage"
APPIMAGETOOL="$TOOLS/appimagetool-${ARCH}.AppImage"

cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
    echo "Falta el venv en $ROOT/.venv" >&2
    exit 1
fi

if [[ ! -x "$ROOT/dist/iptv-player/iptv-player" ]]; then
    echo "Construyendo binario con PyInstaller..."
    "$ROOT/.venv/bin/python" -m PyInstaller iptv-player.spec --noconfirm
fi

rm -rf "$APPDIR"
mkdir -p \
    "$APPDIR/usr/bin" \
    "$APPDIR/usr/lib/iptv-player" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
    "$APPDIR/usr/share/doc/iptv-player"

cp "$ROOT/LICENSE" "$ROOT/THIRD_PARTY_NOTICES.md" \
    "$APPDIR/usr/share/doc/iptv-player/"

cp -a "$ROOT/dist/iptv-player/." "$APPDIR/usr/lib/iptv-player/"

cat > "$APPDIR/usr/bin/iptv-player" <<'EOF'
#!/bin/sh
set -e
APPDIR="${APPDIR:-$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")}"
export LD_LIBRARY_PATH="$APPDIR/usr/lib/iptv-player:$APPDIR/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$APPDIR/usr/lib/iptv-player/iptv-player" "$@"
EOF
chmod 755 "$APPDIR/usr/bin/iptv-player"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
set -e
APPDIR="$(dirname "$(readlink -f "$0")")"
export APPDIR
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"

LDCONFIG="$(command -v ldconfig || true)"

if [ -z "$LDCONFIG" ]; then
    LDCONFIG=/sbin/ldconfig
fi

if ! "$LDCONFIG" -p 2>/dev/null | grep -q 'libmpv\.so\.2'; then
    MESSAGE="IPTV Player necesita libmpv. En Debian/Ubuntu: sudo apt install libmpv2"
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --text="$MESSAGE" || true
    else
        echo "$MESSAGE" >&2
    fi
    exit 1
fi

exec "$APPDIR/usr/bin/iptv-player" "$@"
EOF
chmod 755 "$APPDIR/AppRun"

cp "$ROOT/app/ui/assets/iptv-player.svg" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps/iptv-player.svg"
cp "$ROOT/app/ui/assets/iptv-player.svg" "$APPDIR/iptv-player.svg"
magick "$ROOT/app/ui/assets/iptv-player.svg" -background none -resize 256x256 \
    "$APPDIR/iptv-player.png"
ln -sf iptv-player.png "$APPDIR/.DirIcon"

cat > "$APPDIR/iptv-player.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=IPTV Player
Comment=Reproductor de canales IPTV con modo TV
Exec=iptv-player
Icon=iptv-player
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=iptv;tv;m3u;player;
StartupNotify=true
StartupWMClass=iptv-player
X-AppImage-Version=1.0.0
EOF

cp "$APPDIR/iptv-player.desktop" "$APPDIR/usr/share/applications/iptv-player.desktop"

mkdir -p "$TOOLS" "$ROOT/dist"

if [[ ! -x "$APPIMAGETOOL" ]]; then
    echo "Descargando appimagetool..."
    curl -L --fail --output "$APPIMAGETOOL" \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

export ARCH
export VERSION
export APPIMAGE_EXTRACT_AND_RUN=1

"$APPIMAGETOOL" --no-appstream "$APPDIR" "$APPIMAGE"

echo "AppImage: $APPIMAGE"
