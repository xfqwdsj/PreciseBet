import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import click
import pandas as pd
from fake_useragent import UserAgent

from data import save_to_csv, get_team_value, get_match_handicap
from util import sleep

actions = {'value': '球队价值', 'handicap': '亚盘', }


@click.command()
@click.pass_context
@click.argument('action', type=click.Choice(['value', 'handicap']))
@click.option('--debug', '-d', help='调试模式', is_flag=True)
@click.option('--volume-number', '-v', help='期数', prompt='请输入期数', type=int)
@click.option('--interval', '-i', help='更新间隔（秒）', default=5, type=int)
@click.option('--long-interval', '-l', help='长时间更新间隔（秒）', default=60, type=int)
@click.option('--long-interval-probability', '-p', help='长时间更新间隔概率（0-1）', default=0.025, type=float)
@click.option('--interval_offset-range', '-o', help='更新间隔偏移量范围（秒）', default=2, type=int)
@click.option('--random-ua', '-u', help='随机 UA', is_flag=True)
@click.option('--break-hours', '-b', help='指定要跳过多少小时后的未开始的比赛（时）', default=6, type=int)
@click.option('--only-new', '-n', help='只更新从未获取过的比赛', is_flag=True)
def update(ctx, action: str, debug: bool, volume_number: int, interval: int, long_interval: int,
           long_interval_probability: float, interval_offset_range: int, random_ua: bool, break_hours: int,
           only_new: bool):
    project_path: Path = ctx.obj['project_path']

    click.echo('正在读取数据...')
    global_data = pd.read_csv(project_path / str(volume_number) / 'data.csv', index_col='代号')
    data = pd.read_csv(project_path / str(volume_number) / '{}.csv'.format(action), index_col='代号')
    team_data = pd.read_csv(project_path / 'team.csv', index_col='代号')

    break_time = (datetime.now(timezone.utc) + timedelta(hours=break_hours)).timestamp()

    processing_data = data.copy()[[]]
    processing_data['状态'] = global_data['状态']
    processing_data['更新时间'] = data['更新时间']
    processing_data = processing_data.loc[data['已固定'] == False]
    processing_data = processing_data.loc[(global_data['状态'] != 0) | (global_data['比赛时间'] < break_time)]
    if only_new:
        processing_data = processing_data.loc[processing_data['更新时间'] == -1.0]
    processing_data.sort_values(by=['状态', '更新时间'], ascending=[False, True], inplace=True)

    if debug:
        save_to_csv(processing_data, project_path, 'processing')

    action_name = actions[action]
    new_match_count = len(processing_data.loc[processing_data['更新时间'] == -1.0])
    click.echo('开始更新 {} 信息，有 {} 场比赛从未获取过 {} ...'.format(action_name, new_match_count, action_name))

    long_interval_used_count = 0
    ua = UserAgent().random

    with click.progressbar(processing_data.index, show_pos=True) as indexes:
        for match_id in indexes:
            host_name = team_data.loc[global_data.loc[match_id, '主队'], '名称']
            guest_name = team_data.loc[global_data.loc[match_id, '客队'], '名称']

            click.echo(
                '正在更新代号为 {} 的比赛（{} VS {}）的 {} 信息...'.format(match_id, host_name, guest_name, action_name))

            if data.loc[match_id, '更新时间'] == -1.0:
                click.echo('该场比赛为从未获取过 {} 的比赛'.format(action_name))

            if action == 'value':
                for column in ['主队', '客队']:
                    value = get_team_value(global_data.loc[match_id, column], ua)
                    updated_time = datetime.now(timezone.utc).timestamp()
                    data.loc[match_id, column + '价值'] = value
                    data.loc[match_id, '更新时间'] = updated_time
                    team_data.loc[global_data.loc[match_id, column], '价值'] = value
                    team_data.loc[global_data.loc[match_id, column], '更新时间'] = updated_time
            elif action == 'handicap':
                handicap = get_match_handicap(match_id)
                updated_time = datetime.now(timezone.utc).timestamp()
                data.loc[match_id, ['平即盘1', '平即水', '平即盘2', '平初盘1', '平初水', '平初盘2',
                                    '更新时间']] = handicap + [updated_time]

            if global_data.loc[match_id]['状态'] != 0:
                data.loc[match_id, '已固定'] = True
                click.echo('已固定该场比赛的 {} 信息'.format(action_name))

            save_to_csv(data, project_path / str(volume_number), action)

            if action == 'value':
                save_to_csv(team_data, project_path, 'team')

            if random.random() < long_interval_probability:
                click.echo('随机数命中，将使用长时间更新间隔（概率：{}）'.format(long_interval_probability))
                sleep(long_interval, interval_offset_range)
                long_interval_used_count += 1
            else:
                sleep(interval, interval_offset_range)

            if random_ua:
                ua = UserAgent().random

    click.echo('更新完成，应用了长时间更新间隔的次数：{}'.format(long_interval_used_count))
