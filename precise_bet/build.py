#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.
import os

import PyInstaller.__main__
from pyinstaller_versionfile import create_versionfile

import precise_bet


def build():
    os.system('poetry dynamic-versioning')
    create_versionfile(output_file='version_file.txt', version=precise_bet.__version__,
                       company_name='LTFan (aka xfqwdsj)', file_description='Precise Bet', internal_name='Precise Bet',
                       legal_copyright='Copyright (C) 2023', original_filename='precise_bet.exe',
                       product_name='Precise Bet')
    PyInstaller.__main__.run(['main.spec', '--noconfirm'])
