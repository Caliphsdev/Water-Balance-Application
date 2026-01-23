# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
added_files = [
    ('config/*.yaml', 'config'),
    ('data/*.json', 'data'),
    ('data/diagrams/*.json', 'data/diagrams'),
    ('logo/*.ico', 'logo'),
    ('logo/*.png', 'logo'),
    ('docs/FUTURE_FEATURES_ROADMAP_2026.md', 'docs'),
    ('docs/FUTURE_FEATURES_ONE_PAGE_SUMMARY.md', 'docs'),
    ('README.md', '.'),
    ('LICENSE.txt', '.'),
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'ttkthemes',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell._writer',
        'pandas',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'google.oauth2',
        'google.oauth2.credentials',
        'google.auth',
        'google.auth.transport.requests',
        'googleapiclient',
        'googleapiclient.discovery',
        'sqlite3',
        'json',
        'datetime',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'test',
        '_pytest',
        'setuptools',
        'pip',
        'wheel',
    ],
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
    name='WaterBalance',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windows GUI application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo/Water Balance.ico',  # Application icon
    version_file=None,  # Optional: add version_info.txt if needed
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WaterBalance',
)
