#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from pathlib import Path
from typing import Annotated, Optional

import requests
import typer
from requests import RequestException

from precise_bet import rprint, rprint_err
from precise_bet.data import parse_table
from precise_bet.util import request_content


def generate_data(
    ctx: typer.Context,
    volume_number: Annotated[
        Optional[int], typer.Option("--volume-number", "-v", help="期号")
    ] = None,
    request_trying_times: Annotated[
        int,
        typer.Option("--request-trying-times", help="请求尝试次数（设为 0 无限尝试）"),
    ] = 1,
):
    """生成数据"""

    project_path: Path = ctx.obj["project_path"]
    session: requests.Session = ctx.obj["session"]

    rprint("正在获取数据...")

    text: str
    try:
        text = request_content(
            f"https://live.500.com/zqdc.php{f'?e={volume_number}' if volume_number else ''}",
            session,
            encoding="gb2312",
            trying_times=request_trying_times,
        )
    except RequestException as e:
        rprint_err(e)
        return

    rprint("正在解析数据...")

    data_table = parse_table(project_path, text)

    rprint(f"解析成功，期号：{data_table.volume_number}")

    data_table.data.save()
    data_table.score.save()
    data_table.value.save()
    data_table.handicap.save()
    data_table.sp.save()
    data_table.odd.save()
    data_table.league.save()
    data_table.team.save()
