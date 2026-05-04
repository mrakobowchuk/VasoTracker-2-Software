# -*- mode: python ; coding: utf-8 -*-
# macOS PyInstaller spec for VasoTracker 2
# Build with: pyinstaller vasotracker_2_macos.spec

import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

import os

# Ensure the current directory of the spec file is the working directory
spec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, spec_dir)

import version
from version import __version__

added_files = [
    ("music", "music"),
    ("images", "images"),
    ("SampleData", "SampleData"),
    ("settings.toml", "."),
    ("MMConfig.cfg", "."),
    ("Basler.cfg", "."),
    ("VasoTrackerblue.json", "."),
    ("pacman", "pacman"),
    ("space-invaders", "space-invaders"),
]

a = Analysis(
    ["vasotracker_2.py"],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=["scipy"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=f"vasotracker_{__version__}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f"vasotracker_{__version__}",
)
app = BUNDLE(
    coll,
    name=f"VasoTracker_{__version__}.app",
    # Place a VasoTracker.icns file alongside this spec to set the app icon.
    # icon="images/VasoTracker.icns",
    bundle_identifier="com.vasotracker.vasotracker2",
)
