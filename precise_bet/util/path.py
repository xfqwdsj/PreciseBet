#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from pathlib import Path

from precise_bet import rprint_err


def mkdir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
    elif not path.is_dir():
        rprint_err('路径错误')
        return


def can_write(path: Path):
    exists = path.exists()
    try:
        with path.open(mode='a') as f:
            f.close()
            if not exists:
                path.unlink()
            return True
    except PermissionError:
        return False
