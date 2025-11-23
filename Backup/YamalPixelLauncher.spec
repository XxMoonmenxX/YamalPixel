block_cipher = None

a = Analysis(
    ['YamalPixel-Launcher_V_0.6.722.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.')],
    hiddenimports=[
        'asyncio',
        'asyncio.windows_events', 
        'pygame._freetype',
        'pygame._window',
        'psutil._psutil_windows',
        'pypresence',
        'minecraft_launcher_lib',
        'mcstatus.java_async',
        'mcstatus.bedrock_async',
        'encodings',
        'encodings.utf_8',
        'encodings.cp1251'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    a.zipfiles,
    a.datas,
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