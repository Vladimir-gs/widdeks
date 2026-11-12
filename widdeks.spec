# -*- mode: python ; coding: utf-8 -*-
"""Build de Widdeks con PyInstaller (modo onedir).

Uso:
    pyinstaller widdeks.spec --noconfirm
"""

import os

from PyInstaller.utils.hooks import collect_submodules

BASE = SPECPATH  # noqa: F821  (inyectado por PyInstaller)
APP_DIR = os.path.join(BASE, "clock-widget")
ICON = os.path.join(APP_DIR, "assets", "widdeks.ico")
FONTS = os.path.join(APP_DIR, "fonts")
VERSION_FILE = os.path.join(BASE, "tools", "version_info.txt")

datas = [(FONTS, "fonts")]

hiddenimports = []
hiddenimports += collect_submodules("winrt")
hiddenimports += collect_submodules("pycaw")

a = Analysis(
    [os.path.join(APP_DIR, "widdeks.py")],
    pathex=[APP_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "unittest", "pydoc"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Widdeks",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
    version=VERSION_FILE,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Widdeks",
)
