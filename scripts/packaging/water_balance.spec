# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

# Get the project root - assume spec file is in scripts/packaging/
# Use environment or construct path from spec location
project_root = Path(__file__).parent.parent.parent if '__file__' in dir() else Path.cwd().parent.parent
if not (project_root / "src").exists():
    # Fallback: use current working directory
    project_root = Path.cwd()

icon_path = project_root / "src" / "ui" / "resources" / "icons" / "Water Balance.ico"

block_cipher = None

a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "config"), "config"),
        (str(project_root / "data" / "balance_check_config.json"), "data"),
        (str(project_root / "data" / "balance_check_flow_categories.json"), "data"),
        (str(project_root / "data" / "column_aliases.json"), "data"),
        (str(project_root / "data" / "excel_flow_links.json"), "data"),
        (str(project_root / "data" / "flow_friendly_names.json"), "data"),
        (str(project_root / "data" / "supabase_schema.sql"), "data"),
        (str(project_root / "data" / "diagrams"), "data/diagrams"),
        (str(project_root / "data" / "migrations"), "data/migrations"),
        (str(project_root / "data" / "sqlite_migrations"), "data/sqlite_migrations"),
    ],
    hiddenimports=[],
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
    name="WaterBalanceDashboard",
    icon=str(icon_path),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WaterBalanceDashboard",
)
