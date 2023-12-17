#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import hashlib
import os
import sys
from pathlib import Path

import PyInstaller.__main__
import semver
from pyinstaller_versionfile import create_versionfile

import precise_bet


def build():
    working_dir = Path(__file__).parent

    os.system('poetry dynamic-versioning')
    # 使用命令方式调用，使动态版本在代码中更新的值生效
    os.system(f'{sys.executable} -c "from precise_bet import build; build.start_building(r\'{working_dir}\')"')


def start_building(working_dir: str):
    """要使 `__version__` 为最新值，需使用命令方式重新调用本方法"""

    working_dir = Path(working_dir)

    semver_version = semver.Version.parse(precise_bet.__version__)
    version = semver_version.replace(prerelease=None, build=None)
    version_hash = int(hashlib.sha256(f'{semver_version.prerelease}{semver_version.build}'.encode()).hexdigest(), 16)
    version = f'{version}.{version_hash}'
    create_versionfile(
        output_file=working_dir / 'version_file.txt', version=version, company_name=precise_bet.__author__,
        file_description=f'PreciseBet {precise_bet.__version__}', internal_name='PreciseBet',
        legal_copyright=precise_bet.__copyright__, original_filename='precise_bet.exe', product_name='PreciseBet',
        translations=[0x0804, 1200]
    )
    py_file = working_dir / 'buildfile.py'
    spec_file = working_dir / 'buildfile.spec'
    if spec_file.exists():
        spec_file.unlink()
    if py_file.exists():
        py_file.rename(working_dir / 'buildfile.spec')
    if not spec_file.exists():
        raise FileNotFoundError('未找到 buildfile.spec 文件')
    PyInstaller.__main__.run([str(working_dir / 'buildfile.spec'), '--noconfirm'])
    spec_file.rename(working_dir / 'buildfile.py')
