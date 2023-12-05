#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import click
import pandas as pd
from click_option_group import optgroup
from fake_useragent import UserAgent

from precise_bet.data import save_to_csv, get_team_value, get_match_handicap, match_status
from precise_bet.util import sleep

actions = {'value': '球队价值', 'handicap': '亚盘'}


@click.command()
@click.pass_context
@click.argument('action', type=click.Choice(['value', 'handicap']))
@click.option('--volume-number', '-v', help='期数', prompt='请输入期数', type=int)
@optgroup.group('调试选项', help='调试选项')
@optgroup.option('--debug', '-d', help='调试模式', is_flag=True)
@optgroup.group('风控选项', help='指定更新时采取的风控机制')
@optgroup.option('--interval', '-i', help='基准更新间隔（秒）', default=5, type=int)
@optgroup.option('--extra-interval', '-e', help='额外更新间隔（秒）', default=60, type=int)
@optgroup.option('--long-interval-probability', '-p', help='额外更新间隔概率（0-1）', default=0.025, type=float)
@optgroup.option('--interval-offset-range', '-r', help='更新间隔偏移量范围（秒）', default=2, type=int)
@optgroup.option('--random-ua', help='随机 UA', is_flag=True)
@optgroup.group('更新选项', help='指定更新时采取的策略')
@optgroup.option('--break-hours', '-b', help='指定要跳过多少小时后的未开始的比赛（设为 0 以更新全部，时）', default=6,
                 type=int)
@optgroup.option('--only-new', '-n', help='只更新从未获取过的比赛', is_flag=True)
@optgroup.option('--ignore-fixed', help='不更新已固定的比赛', is_flag=True)
@optgroup.option('--limit-status', '-s', help='指定要更新哪些状态的比赛（以逗号分隔）', type=str)
@optgroup.option('--limit-count', '-m', help='指定要更新多少场比赛（设为 0 以更新与策略匹配的全部比赛）', default=0,
                 type=int)
def update(ctx, action: str, debug: bool, volume_number: int, interval: int, extra_interval: int,
           long_interval_probability: float, interval_offset_range: int, random_ua: bool, break_hours: int,
           only_new: bool, ignore_fixed: bool, limit_status: str | None, limit_count: int):
    """
    更新数据

    更新数据的作用是获取最新的比赛信息，包括球队价值和亚盘

    更新数据采取的策略是比赛状态更高的比赛优先更新，比赛状态相同时，距上次更新时间更长的比赛优先更新

    要获取比赛状态列表，请使用 `precise_bet print-match-status-codes` 命令

    频繁更新大量数据可能会导致被封禁。建议在正常工作时间进行更新并在时间允许的情况下使用命令行选项延长更新间隔

    比赛开始（状态 ≠ 0）后，球队价值及亚盘信息将不再更新，但是仍然可以通过 `--ignore-fixed` 选项更新这些信息

    ## 延长更新间隔

    基准更新间隔为 5 秒，额外更新间隔为 60 秒，额外更新间隔概率为 0.025，更新间隔偏移量范围为 2 秒。这意味着每次更新将使用 5 ± 2 秒的间\
隔，但是有 2.5% 的概率使用 60 ± 2 秒的间隔

    ## 减少更新次数

    通过 `--break-hours` 选项可以指定要跳过多少小时后的未开始的比赛。默认情况下，跳过 6 小时后的未开始的比赛

    通过 `--only-new` 标志可以只更新从未获取过的比赛，这样可以进一步减少更新次数，但是可能会降低数据的即时性

    通过 `--limit-status` 选项可以指定要更新的比赛的状态。默认情况下，更新与策略匹配的全部比赛

    通过 `--limit-count` 选项可以指定要更新多少场比赛。默认情况下，更新与策略匹配的全部比赛
    """

    project_path: Path = ctx.obj['project_path']

    click.echo('正在读取数据...')
    global_data = pd.read_csv(project_path / str(volume_number) / 'data.csv', index_col='代号')
    data = pd.read_csv(project_path / str(volume_number) / f'{action}.csv', index_col='代号')
    team_data = pd.read_csv(project_path / 'team.csv', index_col='代号')

    break_time = (datetime.now() + timedelta(hours=break_hours)).timestamp()
    status_list: list[int] = []

    processing_data = data.copy()[[]]
    processing_data['状态'] = global_data['状态']
    processing_data['更新时间'] = data['更新时间']
    if not ignore_fixed:
        processing_data = processing_data.loc[data['已固定'] == False]
    processing_data = processing_data.loc[(global_data['状态'] != 0) | (global_data['比赛时间'] < break_time)]
    if only_new:
        processing_data = processing_data.loc[processing_data['更新时间'] == -1.0]
    if limit_status is not None:
        status_list = [int(status.strip()) for status in limit_status.split(',')]
        status_list.sort()
        processing_data = processing_data.loc[processing_data['状态'].isin(status_list)]
    processing_data.sort_values(by=['状态', '更新时间'], ascending=[False, True], inplace=True)

    if limit_count > 0:
        processing_data = processing_data.iloc[:limit_count]

    if debug:
        save_to_csv(processing_data, project_path, 'processing')

    data_analysis = pd.DataFrame(columns=['数量'])
    data_analysis.loc['全部'] = len(processing_data)
    data_analysis.loc['从未获取'] = len(processing_data.loc[processing_data['更新时间'] == -1.0])
    data_analysis.loc['已固定'] = len(processing_data.loc[data['已固定'] == True])
    for status in processing_data['状态'].unique():
        data_analysis.loc[match_status[status]] = len(processing_data.loc[processing_data['状态'] == status])

    click.echo()

    click.echo('处理数据分析：')
    click.echo(data_analysis)

    click.echo()

    click.echo(f'本次更新将采取基准更新间隔 {click.style(str(interval), fg="blue", bold=True)} 秒，', nl=False)
    click.echo(f'额外更新间隔 {click.style(str(extra_interval), fg="blue", bold=True)} 秒，', nl=False)
    click.echo(f'使用额外更新间隔的概率 {click.style(str(long_interval_probability), fg="blue", bold=True)}，', nl=False)
    click.echo(f'更新间隔偏移量范围 {click.style(str(interval_offset_range), fg="blue", bold=True)} 秒，', nl=False)
    if break_hours > 0:
        click.echo(f'跳过 {click.style(str(break_hours), fg="blue", bold=True)} 小时后的未开始的比赛，', nl=False)
    else:
        click.echo('不跳过未开始的比赛，', nl=False)
    if only_new:
        click.echo(f'{click.style('只更新从未获取过的比赛', fg='yellow', bold=True)}，', nl=False)
    else:
        click.echo('不对比赛是否已获取过进行限制，', nl=False)
    click.echo(f'{click.style('更新', fg='yellow', bold=True) if ignore_fixed else '不更新'}已固定的比赛，', nl=False)
    if len(status_list) > 0:
        status_text_list = [match_status[status] for status in status_list]
        click.echo(f'只更新状态为 {click.style(status_text_list, fg="yellow", bold=True)} 的比赛，', nl=False)
    else:
        click.echo('不对比赛状态进行限制，', nl=False)
    if limit_count > 0:
        click.echo(f'只更新 {click.style(str(limit_count), fg="yellow", bold=True)} 场比赛')
    else:
        click.echo('不对更新数量进行限制')

    click.echo()

    action_name = actions[action]
    click.echo(f'开始更新{action_name}信息...')

    long_interval_used_count = 0
    ua = UserAgent().random

    start_time = datetime.now()
    initial_eta = timedelta(
        seconds=(interval * (1 - long_interval_probability) + extra_interval * long_interval_probability + 1) * (
            len(processing_data)))

    with click.progressbar(processing_data.index, show_eta=False, show_percent=True, show_pos=True) as indexes:
        for index, match_id in enumerate(indexes):
            eta = timedelta(seconds=(interval * (
                    1 - long_interval_probability) + extra_interval * long_interval_probability + 1) * (
                                            len(processing_data) - index))
            click.echo(f'   预计全部更新还需要 {eta}')

            host_name = team_data.loc[global_data.loc[match_id, '主队'], '名称']
            guest_name = team_data.loc[global_data.loc[match_id, '客队'], '名称']
            status = click.style(match_status[global_data.loc[match_id, '状态']], fg='blue', bold=True)

            click.echo(
                f'正在更新代号为 {match_id} 的比赛（{host_name} VS {guest_name}，{status}）的{action_name}信息...')

            if data.loc[match_id, '更新时间'] == -1.0:
                click.echo(f'该场比赛为从未获取过{action_name}的比赛')

            before: Any
            after: Any

            if action == 'value':
                before = data.loc[match_id, ['主队价值', '客队价值']].tolist()
                after = []
                updated_time: float
                for column in ['主队', '客队']:
                    value = get_team_value(global_data.loc[match_id, column], ua)
                    after += [value]
                    updated_time = datetime.now(timezone.utc).timestamp()
                    team_data.loc[global_data.loc[match_id, column], '价值'] = value
                    team_data.loc[global_data.loc[match_id, column], '更新时间'] = updated_time
                data.loc[match_id, ['主队价值', '客队价值', '更新时间']] = after + [updated_time]
            elif action == 'handicap':
                before = data.loc[match_id, ['平即水1', '平即盘', '平即水2', '平初水1', '平初盘', '平初水2']].tolist()
                after = get_match_handicap(match_id)
                updated_time = datetime.now(timezone.utc).timestamp()
                data.loc[
                    match_id, ['平即水1', '平即盘', '平即水2', '平初水1', '平初盘', '平初水2', '更新时间']] = after + [
                    updated_time]

            if before == after:
                click.echo(f'该场比赛的{action_name}信息未发生变化')
                click.echo('当前：')
            else:
                click.echo(f'该场比赛的{action_name}信息已更新')
                click.echo('更新前：')
                click.secho(str(before), fg='red')
                click.echo('更新后：')
            click.secho(str(after), fg='blue', bold=True)

            if global_data.loc[match_id]['状态'] != 0:
                data.loc[match_id, '已固定'] = True
                click.secho(f'已固定该场比赛的{action_name}信息', fg='yellow', bold=True)

            save_to_csv(data, project_path / str(volume_number), action)

            if action == 'value':
                save_to_csv(team_data, project_path, 'team')

            if index == len(processing_data) - 1:
                break

            if random.random() < long_interval_probability:
                click.secho(f'随机数命中，将使用额外更新间隔（概率：{long_interval_probability}）', fg='yellow')
                sleep(extra_interval, interval_offset_range)
                long_interval_used_count += 1
            else:
                sleep(interval, interval_offset_range)

            if random_ua:
                ua = UserAgent().random

    used_time = datetime.now() - start_time
    click.echo(f'更新完成，用时 {used_time}，', nl=False)
    if used_time > initial_eta:
        click.echo(f'{click.style("超出", fg="yellow")}预计时间 {used_time - initial_eta}，', nl=False)
    elif used_time < initial_eta:
        click.echo(f'{click.style("少于", fg="blue")}预计时间 {initial_eta - used_time}，', nl=False)
    else:
        click.secho('正巧与预计时间相等，', fg='green', bold=True, nl=False)
    click.echo(f'使用额外更新间隔 {long_interval_used_count} 次')
