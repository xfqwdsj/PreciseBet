#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from datetime import datetime
from pathlib import Path

import click
import pandas as pd
from click_option_group import optgroup

from precise_bet.data import match_status, save_to_csv, save_to_excel


@click.command()
@click.pass_context
@optgroup.group('导出选项', help='指定导出时使用的选项')
@optgroup.option('--file-name', '-n', help='导出文件名', default='data', type=str)
@optgroup.option('--file-format', '-f', help='导出文件格式', prompt='请输入文件格式', default='csv',
                 type=click.Choice(['csv', 'excel']))
@optgroup.group('其他选项', help='其他选项')
@optgroup.option('--special-format', '-s', help='使用特殊格式', is_flag=True)
def export(ctx, file_name: str, file_format: str, special_format: bool):
    """
    导出数据
    """

    project_path: Path = ctx.obj['project_path']

    click.echo('开始导出数据...')

    data = pd.DataFrame(columns=['代号']).set_index('代号')

    team = pd.read_csv(project_path / 'team.csv', index_col='代号')

    for volume in project_path.iterdir():
        if not volume.is_dir():
            continue

        volume_number = int(volume.name)

        click.echo(f'正在处理第 {volume_number} 期数据...')

        volume_data = pd.read_csv(volume / 'data.csv', index_col='代号')
        value = pd.read_csv(volume / 'value.csv', index_col='代号')
        handicap = pd.read_csv(volume / 'handicap.csv', index_col='代号')

        volume_data.insert(0, '期数', volume_number)
        volume_data['主队价值'] = value['主队价值']
        volume_data['客队价值'] = value['客队价值']
        volume_data['平即水1'] = handicap['平即水1']
        volume_data['平即盘'] = handicap['平即盘']
        volume_data['平即水2'] = handicap['平即水2']
        if special_format:
            volume_data['空列1'] = ''
            volume_data['空列2'] = ''
        volume_data['平初水1'] = handicap['平初水1']
        volume_data['平初盘'] = handicap['平初盘']
        volume_data['平初水2'] = handicap['平初水2']

        data = pd.concat([data, volume_data])

    timezone = datetime.now().astimezone().tzinfo

    data['比赛时间'] = pd.to_datetime(data['比赛时间'], unit='s', utc=True).dt.tz_convert(timezone)
    data['状态'] = data['状态'].map(match_status)
    data['主队'] = data['主队'].map(team['名称'])
    data['客队'] = data['客队'].map(team['名称'])

    if file_format == 'csv':
        save_to_csv(data, project_path, file_name)
    elif file_format == 'excel':
        data['比赛时间'] = data['比赛时间'].dt.tz_localize(None)
        save_to_excel(data, project_path, file_name)
