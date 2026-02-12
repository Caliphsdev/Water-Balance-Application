# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules
import nacl
import cffi

# Get the project root - assume spec file is in scripts/packaging/
# Use environment or construct path from spec location
project_root = Path(__file__).parent.parent.parent if '__file__' in dir() else Path.cwd().parent.parent
if not (project_root / "src").exists():
    # Fallback: use current working directory
    project_root = Path.cwd()

icon_path = project_root / "src" / "ui" / "resources" / "icons" / "Water Balance.ico"

block_cipher = None

hiddenimports = collect_submodules("nacl")
hiddenimports.append("_cffi_backend")
binaries = collect_dynamic_libs("nacl")
nacl_path = Path(nacl.__file__).parent
sodium_pyd = nacl_path / "_sodium.pyd"
if sodium_pyd.exists():
    binaries.append((str(sodium_pyd), "nacl"))
libsodium_dir = nacl_path / ".libs"
if libsodium_dir.exists():
    for candidate in libsodium_dir.glob("libsodium*.dll"):
        binaries.append((str(candidate), "nacl"))
for candidate in nacl_path.glob("libsodium*.dll"):
    binaries.append((str(candidate), "nacl"))

cffi_site = Path(cffi.__file__).parent.parent
for candidate in cffi_site.glob("_cffi_backend*.pyd"):
    binaries.append((str(candidate), "."))

datas = [
    (str(project_root / "config"), "config"),
    (str(project_root / "data" / "water_balance.db"), "data"),
    (str(project_root / "data" / "balance_check_config.json"), "data"),
    (str(project_root / "data" / "balance_check_flow_categories.json"), "data"),
    (str(project_root / "data" / "column_aliases.json"), "data"),
    (str(project_root / "data" / "flow_friendly_names.json"), "data"),
    (str(project_root / "data" / "supabase_schema.sql"), "data"),
    (str(project_root / "data" / "diagrams"), "data/diagrams"),
    (str(project_root / "data" / "migrations"), "data/migrations"),
    (str(project_root / "data" / "sqlite_migrations"), "data/sqlite_migrations"),
    (str(project_root / "assets" / "fonts"), "assets/fonts"),
    (str(project_root / "src" / "ui" / "resources" / "icons"), "src/ui/resources/icons"),
]

excel_links = project_root / "data" / "excel_flow_links.json"
if excel_links.exists():
    datas.append((str(excel_links), "data"))

a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    upx_exclude=["_sodium.pyd", "libsodium*.dll", "_cffi_backend*.pyd"],
    name="WaterBalanceDashboard",
)
