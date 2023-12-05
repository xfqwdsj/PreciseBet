#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from pathlib import Path
from typing import Callable

import click
import pandas as pd


def save(data: pd.DataFrame, path: Path, file_name: str, func: Callable):
    click.echo('正在保存数据...')
    if not path.exists():
        path.mkdir()
    elif not path.is_dir():
        click.echo('路径错误', err=True)
        return
    file_path = path / file_name
    click.echo(f'正在保存到 {file_path} ...')
    func(data, file_path)


def save_to_excel(data: pd.DataFrame, path: Path, file_name: str):
    save(data, path, f'{file_name}.xlsx', excel_saver)


def excel_saver(data: pd.DataFrame, path: Path):
    data.to_excel(path)


def save_to_csv(data: pd.DataFrame, path: Path, file_name: str):
    save(data, path, f'{file_name}.csv', csv_saver)


def csv_saver(data: pd.DataFrame, path: Path):
    data.to_csv(path)