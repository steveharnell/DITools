# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['main.py'],
    pathex=['/Users/steveharnell/Desktop/DITools_V2_GTP_temp'],
    binaries=[],
    datas=[],
    hiddenimports=['file_comparator', 'project', 'render_check', 'sync', 'trash', 'tree_generator', 'ui_style', 'main'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DITools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2',
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(exe,
         name='DITools.app',
         icon='main.icns',
         bundle_identifier=None,
         # Add or modify this section:
         info_plist={
             'CFBundleShortVersionString': '2.2.3',
             'CFBundleVersion': '2.2.3',             
             'CFBundleGetInfoString': 'DITools v2.2.3',
             'NSHumanReadableCopyright': 'Copyright © 2025 32Thirteen Productions, LLC'
         })