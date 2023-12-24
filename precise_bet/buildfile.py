# -*- mode: python ; coding: utf-8 -*-
#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from hashlib import sha256

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files
# 用于 `eval` 函数解析 `version`
# noinspection PyUnresolvedReferences
from PyInstaller.utils.win32.versioninfo import *
from pyinstaller_versionfile import MetaData, Writer
from semver import Version

import precise_bet

datas = [('../LICENSE', '.')]
datas += collect_data_files('fake_useragent')

a = Analysis(
    ['main.py'], pathex=[], binaries=[], datas=datas, hiddenimports=['shellingham.nt', 'shellingham.posix', 'tabulate'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False
)

pyz = PYZ(a.pure)

semver_version = Version.parse(precise_bet.__version__)
version_hash = int(sha256(f'{semver_version.prerelease}{semver_version.build}'.encode()).hexdigest(), 16)
version = f'{semver_version.replace(prerelease=None, build=None)}.{version_hash}'

vers_metadata = MetaData(
    version=version, company_name=precise_bet.__author__, file_description=f'PreciseBet {precise_bet.__version__}',
    internal_name='PreciseBet', legal_copyright=precise_bet.__copyright__, original_filename='precise_bet.exe',
    product_name='PreciseBet', translations=[0x0804, 1200]
)

vers_metadata.validate()
vers_metadata.sanitize()

vers_writer = Writer(vers_metadata)

vers_writer.render()

# noinspection PyProtectedMember
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='precise_bet', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False, argv_emulation=False, target_arch=None,
    codesign_identity=None, entitlements_file=None, version=eval(vers_writer._content), contents_directory='files'
)

coll = COLLECT(
    exe, a.binaries, a.datas, strip=False, upx=True, upx_exclude=[], name='precise_bet'
)
