# -*- mode: python ; coding: utf-8 -*-

#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files

datas = [('LICENSE', '.')]
datas += collect_data_files('fake_useragent')

a = Analysis(
    ['main.py'], pathex=[], binaries=[], datas=datas, hiddenimports=['shellingham', 'tabulate'], hookspath=[],
    hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='precise_bet', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False, argv_emulation=False, target_arch=None,
    codesign_identity=None, entitlements_file=None, version='version_file.txt', contents_directory='files'
)

coll = COLLECT(
    exe, a.binaries, a.datas, strip=False, upx=True, upx_exclude=[], name='precise_bet'
)
