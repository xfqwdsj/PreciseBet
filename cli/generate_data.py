from pathlib import Path

import click

from data import parse_table, save_to_csv
from util import request_content


@click.command()
@click.pass_context
@click.option('--volume-number', '-v', help='期数', default=None, type=int)
def generate_data(ctx, volume_number: int | None):
    project_path: Path = ctx.obj['project_path']

    click.echo('正在获取数据...')

    text: str
    try:
        text = request_content('https://live.500.com/zqdc.php' + ('?e={}'.format(volume_number) if volume_number else ''))
    except RuntimeError as err:
        click.echo(err, err=True)
        return

    data_table = parse_table(project_path, text)

    click.echo('解析成功，期数：{}'.format(data_table.volume_number))

    save_to_csv(data_table.data, project_path / str(data_table.volume_number), 'data')
    save_to_csv(data_table.value, project_path / str(data_table.volume_number), 'value')
    save_to_csv(data_table.handicap, project_path / str(data_table.volume_number), 'handicap')
    save_to_csv(data_table.league, project_path, 'league')
    save_to_csv(data_table.team, project_path, 'team')
