#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from pathlib import Path

import click


def mkdir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
    elif not path.is_dir():
        click.echo('路径错误', err=True)
        return
