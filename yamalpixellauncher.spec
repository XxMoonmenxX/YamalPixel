# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Путь к Python DLL (для Python 3.14)
PYTHON_DLL = r"C:\Users\Moonmen\AppData\Local\Programs\Python\Python314\python314.dll"

# Добавляем Python DLL в binaries если файл существует
binaries_list = []
if os.path.exists(PYTHON_DLL):
    binaries_list.append((PYTHON_DLL, '.'))

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries_list,  # ← Добавляем Python DLL
    datas=[
        ('icon.ico', '.'),
        ('ConfDir', 'ConfDir'),
        ('Network', 'Network'),
        ('Ui', 'Ui'),
        ('Core', 'Core'),
        ('MCLIB/version.txt', 'MCLIB'),
        ('YamalPixelRes', 'YamalPixelRes'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'MCLIB',
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
        'Ui.ShaderManager',
        'Ui.DownloadProgress',
        'encodings.utf_8',
        'encodings.cp1251',
        'MCLIB.mod_loader',
        'Network.DependencyManager',
        'Network.java_checker',
        'Network.shader_manager',
        'Network.CurseForgeLoader',
        'Network.Updates',
    ],
    excludes=[
        'tkinter',
        'PyQt5',
        'numpy',
        'pandas',
        'matplotlib',
        'test',
        'unittest',
        'distutils',
        'setuptools',
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
    runtime_tmpdir=None,  # Можно заменить на "C:\\Temp"
    console=False,  # True для отладки, False для релиза
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    onefile=True,
)

# COLLECT не нужен для onefile