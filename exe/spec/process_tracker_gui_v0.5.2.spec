# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\rdaxini\\Documents\\GitHub\\LabProcessTracker\\src\\process_tracker_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\rdaxini\\Documents\\GitHub\\LabProcessTracker\\tools_processes.json', '.'), ('C:\\Users\\rdaxini\\Documents\\GitHub\\LabProcessTracker\\tray_layouts.json', '.')],
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
    name='process_tracker_gui_v0.5.2',
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
