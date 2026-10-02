# -*- mode: python ; coding: utf-8 -*-
# Derleme: önce  python scripts/fetch_ffmpeg.py  (vendor/ klasörüne FFmpeg),
# sonra  python -m PyInstaller AudioVideoConverter.spec  →  dist/AudioVideoConverter/


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('vendor/ffmpeg.exe', 'vendor'), ('vendor/ffprobe.exe', 'vendor')],
    datas=[('assets', 'assets'), ('vendor/FFMPEG-LICENSE.txt', 'vendor'), ('vendor/FFMPEG-README.txt', 'vendor')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AudioVideoConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AudioVideoConverter',
)
