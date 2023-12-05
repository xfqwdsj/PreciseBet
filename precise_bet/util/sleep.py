#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import random
import time

import click


def sleep(time_sec: int, offset_range_sec: int):
    sleep_time = time_sec + random.randint(-offset_range_sec, offset_range_sec)
    if sleep_time < 0:
        sleep_time = 0
    click.echo('等待 {} 秒...'.format(sleep_time))
    time.sleep(sleep_time)
