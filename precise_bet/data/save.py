#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from pathlib import Path
from typing import Callable

from pandas import DataFrame
from pandas.io.formats.style import Styler

from precise_bet import rprint
from precise_bet.util import mkdir


def save_message(path: Path, func: Callable):
    rprint('正在保存数据...')
    mkdir(path.parent)
    rprint(f'正在保存到 [bold]{path}[/bold] ...')
    func()


def save(data: DataFrame | Styler, path: Path, func: Callable):
    save_message(path, lambda: func(data, path))


def save_to_html(data: DataFrame | Styler, path: Path, file_name: str, extension: str = '.html'):
    save(data, path / f'{file_name}{extension}', lambda d, p: d.to_html(p))


def save_to_excel(data: DataFrame | Styler, path: Path, file_name: str, extension: str = '.xlsx'):
    save(data, path / f'{file_name}{extension}', lambda d, p: d.to_excel(p))


def save_to_csv(data: DataFrame, path: Path, file_name: str, extension: str = '.csv'):
    save(data, path / f'{file_name}{extension}', lambda d, p: d.to_csv(p))
