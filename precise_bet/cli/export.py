#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from datetime import datetime
from pathlib import Path

import click
import pandas as pd
from click_option_group import optgroup
from precise_bet.data import match_status, save_to_csv, save_to_excel

result_color = 'color: #FF8080;'
ya_hei = 'font-family: 微软雅黑;'
calibri = 'font-family: Calibri;'
tahoma = 'font-family: Tahoma;'
nine_point = 'font-size: 9pt;'
ten_point = 'font-size: 10pt;'
center = 'text-align: center;'
left = 'text-align: left;'
middle = 'vertical-align: middle;'


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

    league = pd.read_csv(project_path / 'league.csv', index_col='代号')
    team = pd.read_csv(project_path / 'team.csv', index_col='代号')

    for volume in project_path.iterdir():
        if not volume.is_dir():
            continue

        volume_number = int(volume.name)

        click.echo(f'正在处理第 {volume_number} 期数据...')

        volume_data = pd.read_csv(volume / 'data.csv', index_col='代号')
        score = pd.read_csv(volume / 'score.csv', index_col='代号')
        value = pd.read_csv(volume / 'value.csv', index_col='代号')
        handicap = pd.read_csv(volume / 'handicap.csv', index_col='代号')
        odd = pd.read_csv(volume / 'odd.csv', index_col='代号')

        def calculate_result(score_text: str):
            score_list = score_text.split('-')
            host_score = int(score_list[0].strip())
            guest_score = int(score_list[1].strip())
            if host_score > guest_score:
                return '胜'
            elif host_score == guest_score:
                return '平'
            else:
                return '负'

        volume_data.insert(0, '期数', volume_number)
        volume_data.insert(7, '比分',
                           score['主队'].astype(int).astype(str) + ' - ' + score['客队'].astype(int).astype(str))
        volume_data['胜'] = odd['胜']
        volume_data['平'] = odd['平']
        volume_data['负'] = odd['负']
        volume_data['结果'] = volume_data['比分'].apply(calculate_result)
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
    data['主队'] = data['主队'].map(team['名称'])
    data['客队'] = data['客队'].map(team['名称'])

    status = data['状态'].map(match_status)
    if special_format:
        data.drop(columns=['状态'], inplace=True)
    data['状态'] = status

    if file_format == 'csv':
        data['赛事'] = data['赛事'].map(league['名称'])
        save_to_csv(data, project_path, file_name)
    elif file_format == 'excel':
        data['比赛时间'] = data['比赛时间'].dt.tz_localize(None)
        league_styles = data['赛事'].map(league['颜色'])
        league_styles = league_styles.apply(lambda x: f'color: white;background-color: {x};'
                                                      f'{ya_hei}{nine_point}{center}{middle}')
        data['赛事'] = data['赛事'].map(league['名称'])

        odd_style = f'{calibri}{ten_point}{center}{middle}'
        style_win = [('background-color: #F4B084;' if r == '胜' else '') + odd_style for r in data['结果']]
        style_draw = [('background-color: #F4B084;' if r == '平' else '') + odd_style for r in data['结果']]
        style_lose = [('background-color: #F4B084;' if r == '负' else '') + odd_style for r in data['结果']]

        length = len(data)
        style = data.style
        style.apply(lambda _: [f'{ya_hei}{nine_point}{center}{middle}'] * length, subset=['期数', '场次'])
        style.apply(lambda _: league_styles, subset=['赛事'])
        style.apply(lambda _: [f'{nine_point}{middle}'] * length, subset=['轮次'])
        style.apply(lambda _: [f'{calibri}{nine_point}{middle}'] * length, subset=['比赛时间'])
        style.apply(lambda _: [f'{ten_point}{middle}'] * length, subset=['主队', '客队'])
        style.apply(lambda _: [f'{calibri}{result_color}{ten_point}{center}{middle}'] * length, subset=['比分'])
        style.apply(lambda _: [f'{ya_hei}{result_color}{nine_point}{center}{middle}'] * length, subset=['结果'])
        style.apply(lambda _: style_win, subset=['胜'])
        style.apply(lambda _: style_draw, subset=['平'])
        style.apply(lambda _: style_lose, subset=['负'])
        style.apply(lambda _: [f'{left}{middle}'] * length, subset=['主队价值', '客队价值'])
        style.apply(lambda _: [f'{tahoma}{nine_point}{center}{middle}'] * length,
                    subset=['平初水1', '平初盘', '平初水2', '平即水1', '平即盘', '平即水2'])
        save_to_excel(style, project_path, file_name)
