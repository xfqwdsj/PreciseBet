#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from pathlib import Path

import click

from precise_bet.data import parse_table
from precise_bet.util import request_content


@click.command()
@click.pass_context
@click.option('--volume-number', '-v', help='期号', default=None, type=int)
def generate_data(ctx, volume_number: int | None):
    """
    生成数据

    生成数据的作用是建立总表，同步最新的比赛信息以便进一步获取数据
    """

    project_path: Path = ctx.obj['project_path']

    click.echo('正在获取数据...')

    text: str
    try:
        text = request_content(f'https://live.500.com/zqdc.php{f'?e={volume_number}' if volume_number else ''}')
    except RuntimeError as err:
        click.echo(err, err=True)
        return

    click.echo('正在解析数据...')

    data_table = parse_table(project_path, text)

    click.echo(f'解析成功，期号：{data_table.volume_number}')

    data_table.data.save()
    data_table.score.save()
    data_table.value.save()
    data_table.handicap.save()
    data_table.odd.save()
    data_table.league.save()
    data_table.team.save()
