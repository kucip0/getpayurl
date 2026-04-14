# -*- mode: python ; coding: utf-8 -*-

import certifi

a = Analysis(
    ['auto_order_4yuns.py'],
    pathex=[],
    binaries=[],
    datas=[('login_4yuns.py', '.'), (certifi.where(), 'certifi')],
    hiddenimports=['certifi', 'charset_normalizer', 'urllib3'],
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
    a.binaries,
    a.datas,
    [],
    name='autoPayQR_4yuns',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)
