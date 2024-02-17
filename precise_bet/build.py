#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import os
import sys
from pathlib import Path

import PyInstaller.__main__

working_dir = Path(__file__).parent


def build():
    start_building(False)


def build_one_file():
    start_building(True)


def start_building(one_file: bool):
    os.system('git reset HEAD --hard')
    os.system('poetry dynamic-versioning')

    # 使用命令方式调用，使动态版本在代码中更新的值生效
    os.system(f'{sys.executable} -c "from precise_bet import build; build._build(r\'{working_dir}\', {one_file})"')


def _build(working_dir_str: str, one_file: bool):
    """要使 `__version__` 为最新值，需使用命令方式重新调用本方法"""

    working_dir_str = Path(working_dir_str)

    py_file = working_dir_str / 'buildfile.py'
    spec_file = working_dir_str / 'buildfile.spec'
    if spec_file.exists():
        spec_file.unlink()
    if py_file.exists():
        py_file.rename(working_dir_str / 'buildfile.spec')
    if not spec_file.exists():
        raise FileNotFoundError('未找到 buildfile.spec 文件')

    cmd = [str(working_dir_str / 'buildfile.spec'), '--noconfirm']
    if one_file:
        cmd.append('-F')

    PyInstaller.__main__.run(cmd)
    spec_file.rename(working_dir_str / 'buildfile.py')
