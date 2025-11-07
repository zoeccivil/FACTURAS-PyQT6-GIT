# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/Dropbox/PROGAIN/EQUIPOS PyQT6/progain_database-qt.db', '.'), ('C:\\Users\\servi\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\platforms', 'PyQt6\\plugins\\platforms')],
    hiddenimports=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'pandas', 'matplotlib', 'reportlab', 'openpyxl'],
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
    name='alquiler_equipos',
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
)
