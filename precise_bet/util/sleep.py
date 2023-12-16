#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import time
from typing import Callable

from precise_bet import rprint


def _sleep(time_sec: int, after: Callable[[int], None] | None = None):
    if after is None:
        time.sleep(time_sec)
        return

    for i in range(time_sec):
        time.sleep(1)
        after(i)


def sleep(time_sec: int, after: Callable[[int], None] | None = None):
    if time_sec < 0:
        time_sec = 0
    rprint(f'等待 [bold]{time_sec}[/bold] 秒...')
    _sleep(time_sec, after)
