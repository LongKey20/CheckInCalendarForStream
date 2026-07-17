# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

python_root = Path(sys.base_prefix)

a = Analysis(
    ["StreamerTool.py"],
    pathex=[],
    binaries=[
        (str(python_root / "DLLs" / "_tkinter.pyd"), "."),
        (str(python_root / "DLLs" / "tcl86t.dll"), "."),
        (str(python_root / "DLLs" / "tk86t.dll"), "."),
    ],
    datas=[
        ("css/call/default.css", "css/call"),
        ("css/queue/default.css", "css/queue"),
        ("css/calendar/default.css", "css/calendar"),
        ("audio/default.mp3", "audio"),
        ("audio/README.md", "audio"),
        (str(python_root / "Lib" / "tkinter"), "tkinter"),
        (str(python_root / "tcl" / "tcl8.6"), "_tcl_data"),
        (str(python_root / "tcl" / "tk8.6"), "_tk_data"),
    ],
    hiddenimports=["_tkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["pyi_rth_tkinter_local.py"],
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
    name="StreamerTool",
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
