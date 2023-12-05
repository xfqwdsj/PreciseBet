#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.
import hashlib
import os

import PyInstaller.__main__
from pyinstaller_versionfile import create_versionfile

import precise_bet


def full_build():
    os.system('poetry dynamic-versioning')
    build()


def build():
    split_version = precise_bet.__version__.split('-')
    version = f'{split_version[0]}.{int(hashlib.sha256(split_version[1].encode()).hexdigest(), 16) % 1000000}'
    create_versionfile(output_file='version_file.txt', version=version,
                       company_name=precise_bet.__author__, file_description='Precise Bet', internal_name='Precise Bet',
                       legal_copyright=precise_bet.__copyright__, original_filename='precise_bet.exe',
                       product_name='Precise Bet', translations=[0x0804, 1200])
    PyInstaller.__main__.run(['main.spec', '--noconfirm'])
