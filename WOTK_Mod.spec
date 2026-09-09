# PyInstaller spec for the unified GUI. Tesseract remains an external dependency.

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("pynput") + collect_submodules("pygetwindow")

a = Analysis(
    ["src/wotk/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
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
    name="WOTK_Mod",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WOTK_Mod",
)
