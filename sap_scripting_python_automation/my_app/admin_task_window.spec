# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['admin_task_window.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\my_app', 'my_app'), ('..\\my_app\\icons', 'my_app\\icons'), ('..\\my_app\\app_utils', 'my_app\\app_utils'), ('..\\utils', 'utils'), ('..\\transactions', 'transactions')],
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
    a.binaries,
    a.datas,
    [],
    name='admin_task_window',
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
    icon=['..\\Wieland_Sap_Logo.ico'],
)
