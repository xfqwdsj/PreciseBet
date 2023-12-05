#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import hashlib
import os

import PyInstaller.__main__
import semver
from pyinstaller_versionfile import create_versionfile

import precise_bet


def build():
    os.system('poetry dynamic-versioning')
    semver_version = semver.Version.parse(precise_bet.__version__)
    version = semver_version.replace(prerelease=None, build=None)
    version_hash = hashlib.sha256(f'{semver_version.prerelease}{semver_version.build}'.encode()).hexdigest()
    version = f'{version}.{int(version_hash, 16) % 1000000}'
    create_versionfile(output_file='version_file.txt', version=version, company_name=precise_bet.__author__,
                       file_description=f'PreciseBet {precise_bet.__version__}', internal_name='PreciseBet',
                       legal_copyright=precise_bet.__copyright__, original_filename='precise_bet.exe',
                       product_name='PreciseBet', translations=[0x0804, 1200])
    PyInstaller.__main__.run(['main.spec', '--noconfirm'])
