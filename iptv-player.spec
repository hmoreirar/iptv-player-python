# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)
assets = project_root / "app" / "ui" / "assets"

a = Analysis(
    [str(project_root / "app" / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(assets), "app/ui/assets")],
    hiddenimports=[
        "mpv",
        "PySide6.QtSvg",
        "app.favorites",
        "app.m3u.cache",
        "app.m3u.iptv_org",
        "app.m3u.loader",
        "app.m3u.parser",
        "app.player.mpv_player",
        "app.tv_mode",
        "app.ui.icons",
        "app.ui.theme",
        "app.ui.widgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="iptv-player",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="iptv-player",
)
