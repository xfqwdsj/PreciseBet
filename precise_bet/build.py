#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import hashlib
import os
import sys

import PyInstaller.__main__
import semver
from pyinstaller_versionfile import create_versionfile

import precise_bet


def build():
    # os.system('poetry dynamic-versioning')
    # 使用命令方式调用，使动态版本在代码中更新的值生效
    os.system(f'{sys.executable} -c "from precise_bet import build; build.start_building()"')


def start_building():
    # 要使 `__version__` 为最新值，需使用命令方式重新调用本方法
    semver_version = semver.Version.parse(precise_bet.__version__)
    version = semver_version.replace(prerelease=None, build=None)
    version_hash = int(hashlib.sha256(f'{semver_version.prerelease}{semver_version.build}'.encode()).hexdigest(), 16)
    version = f'{version}.{version_hash}'
    create_versionfile(output_file='version_file.txt', version=version, company_name=precise_bet.__author__,
                       file_description=f'PreciseBet {precise_bet.__version__}', internal_name='PreciseBet',
                       legal_copyright=precise_bet.__copyright__, original_filename='precise_bet.exe',
                       product_name='PreciseBet', translations=[0x0804, 1200])
    PyInstaller.__main__.run(['main.spec', '--noconfirm'])
