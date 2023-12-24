#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import os
import sys
from pathlib import Path

import PyInstaller.__main__


def build():
    working_dir = Path(__file__).parent

    os.system('poetry dynamic-versioning')
    # 使用命令方式调用，使动态版本在代码中更新的值生效
    os.system(f'{sys.executable} -c "from precise_bet import build; build.start_building(r\'{working_dir}\')"')


def start_building(working_dir: str):
    """要使 `__version__` 为最新值，需使用命令方式重新调用本方法"""

    working_dir = Path(working_dir)

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
