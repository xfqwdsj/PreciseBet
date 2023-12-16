#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import time

from precise_bet import rprint


def sleep(time_sec: int):
    if time_sec < 0:
        time_sec = 0
    rprint(f'等待 [bold]{time_sec}[/bold] 秒...')
    time.sleep(time_sec)
