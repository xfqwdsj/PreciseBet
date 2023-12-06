#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import time

import click


def sleep(time_sec: int):
    if time_sec < 0:
        time_sec = 0
    click.echo(f'等待 {time_sec} 秒...')
    time.sleep(time_sec)
