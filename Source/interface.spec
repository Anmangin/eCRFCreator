# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\a_mangin\\Documents\\GitHub\\eCRFCreator\\Source\\/Python/interface.py'],
    pathex=[],
    binaries=[],
    datas=[('Python/config.json', 'Python'), ('Python/style.css', 'Python'), ('Python/sidebar.js', 'Python'), ('Python/Template_CRF.html', 'Python'), ('images.ico', 'Python')],
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
    name='interface',
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
    icon=['images.ico'],
)
