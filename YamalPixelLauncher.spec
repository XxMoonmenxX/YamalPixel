# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('ConfDir', 'ConfDir'),
        ('Network', 'Network'),
        ('Ui', 'Ui'),
        ('Core', 'Core'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'minecraft_launcher_lib',
        'mcstatus',
        'pypresence',
        'requests',
        'aiohttp',
        'bs4',
        'pygame',
        'psutil',
        'ConfDir',
        'ConfDir.Configs',
        'ConfDir.ScaleRes',
        'ConfDir.utils',
        'ConfDir.Versions',
        'Network.ModrinthLoader',
        'Network.CurseForgeLoader',
        'Network.Downloader',
        'Core.run',
        'Core.backup',
        'Core.collection_loader',
        'Ui.MainWindow',
        'Ui.collection_manager',
        'Ui.CollectionCreator',
        'Ui.DependencyAnalyzer',
        'Ui.QtDiagnosticWindow',
        'encodings.utf_8',
        'encodings.cp1251',
    ],
    excludes=[
        'tkinter',
        'PyQt5',
        'numpy',
        'pandas',
        'matplotlib',
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
    a.binaries,
    a.datas,
    [],
    name='YamalPixelLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YamalPixelLauncher'
)