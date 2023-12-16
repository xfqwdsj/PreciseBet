#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Generic, Optional, Tuple, TypeVar

import pandas as pd
import typer
from fake_useragent import UserAgent
from rich.console import Console
from rich.markdown import Markdown

from precise_bet import rprint
from precise_bet.data import get_match_handicap, get_team_value, save_to_csv
from precise_bet.type import DataTable, HandicapTable, MatchInformationTable, ProjectTable, TeamTable, UpdatableTable, \
    ValueTable, match_status_dict
from precise_bet.util import sleep

AT = TypeVar('AT', bound=ProjectTable)


class Action(Generic[AT], ABC):
    name: str
    _table: AT

    def __init__(self, name: str):
        self.name = name

    @property
    def table(self) -> AT:
        return self._table.copy()

    @abstractmethod
    def assign(self, **kwargs):
        pass

    def filter(self, **kwargs) -> AT:
        pass

    @abstractmethod
    def update(self, **kwargs) -> Tuple[Any, Any]:
        pass

    def __str__(self):
        return self.name


class ValueAction(Action[ValueTable]):
    def assign(self, project_path: Path, **_):
        self._table = ValueTable(project_path).read()

    def filter(self, indexes, **_):
        return self.table.loc[self.table.index.isin(indexes)]

    def update(self, match_id: str, global_data: DataTable, team_data: TeamTable, ua: str, **_):
        before = self._table.get_data(match_id)
        after = []
        updated_time: float
        for team_id_column in [DataTable.host_id, DataTable.guest_id]:
            value = get_team_value(global_data.loc[match_id, team_id_column], ua)
            after += [value]
            team_data.update_from_value(global_data.loc[match_id, team_id_column], value)
            team_data.save()
        self._table.update_from_list(match_id, after, global_data.loc[match_id, DataTable.match_status])
        self._table.save()
        return before, after

    def __init__(self):
        super().__init__('球队价值')


class HandicapAction(Action[HandicapTable]):
    def assign(self, project_path: Path, **_):
        self._table = HandicapTable(project_path).read()

    def filter(self, indexes, **_):
        return self.table.loc[self.table.index.isin(indexes)]

    def update(self, match_id: str, global_data: DataTable, ua: str, **_):
        before = self._table.get_data(match_id)
        after = get_match_handicap(match_id, ua)
        self._table.update_from_list(match_id, after, global_data.loc[match_id, DataTable.match_status])
        self._table.save()
        return before, after

    def __init__(self):
        super().__init__('亚盘')


class Actions(Enum):
    value_action = ValueAction()
    handicap_action = HandicapAction()


def actions_parser(value: str) -> Action:
    try:
        return Actions[f'{value}_action'].value
    except KeyError:
        raise typer.BadParameter(f'无效的数据类型：{value}')


@dataclass
class Interval:
    seconds: int
    extra: bool


def update(
        ctx: typer.Context,
        action: Annotated[Action, typer.Argument(help='要更新的数据类型', case_sensitive=False, parser=actions_parser)],
        debug: Annotated[bool, typer.Option(help='调试模式')] = False,
        volume_number: Annotated[Optional[int], typer.Option('--volume-number', '-v', help='期号')] = None,
        interval: Annotated[int, typer.Option('--interval', '-i', help='基准更新间隔（秒）')] = 5,
        extra_interval: Annotated[int, typer.Option('--extra-interval', '-e', help='额外更新间隔（秒）')] = 60,
        extra_interval_probability: Annotated[
            float, typer.Option('--extra-interval-probability', '-p', help='额外更新间隔概率（0-1）')] = 0,
        interval_offset_range: Annotated[
            int, typer.Option('--interval-offset-range', '-r', help='更新间隔偏移量范围（秒）')] = 2,
        random_ua: Annotated[bool, typer.Option(help='随机 UA')] = False,
        last_updated_status: Annotated[str, typer.Option(
            help='指定要更新/排除上次更新时是哪些状态的比赛（以逗号分隔，在选项前加 `e` 切换排除模式）'
        )] = '0,1,2,3,12', status: Annotated[str, typer.Option(
            help='指定要更新/排除哪些状态的比赛（以逗号分隔，在选项前加 `e` 切换排除模式）'
        )] = 'e1,2,3,12', break_hours: Annotated[
            int, typer.Option('--break-hours', '-b', help='指定要跳过多少小时后的未开始的比赛（设为 0 以忽略，时）')] = 6,
        only_new: Annotated[bool, typer.Option('--only-new', '-n', help='只更新从未获取过的比赛')] = False,
        limit_count: Annotated[Optional[int], typer.Option('--limit-count', '-m', help='指定要更新多少场比赛')] = None
):
    """更新数据"""

    project_path: Path = ctx.obj['project_path']

    global_data = DataTable(project_path).read()
    team_data = TeamTable(project_path).read()

    if volume_number is not None:
        global_data = global_data.loc[global_data[DataTable.volume_number] == volume_number]

    rprint('正在读取数据...')

    action.assign(project_path=project_path)
    data = action.filter(indexes=global_data.index)

    if break_hours < 0:
        break_hours = 0
    break_time = (datetime.now() + timedelta(hours=break_hours)).timestamp()

    def init_status_list(string: str):
        string = string.strip()
        if string.startswith('e'):
            exclude_list = [int(s.strip()) for s in string[1:].split(',')]
            result = list(set(match_status_dict.keys()) - set(exclude_list))
        else:
            result = [int(s.strip()) for s in string.split(',')]
        result.sort()
        return result

    last_updated_status_list: list[int] = [-1] + init_status_list(last_updated_status)
    status_list: list[int] = init_status_list(status)

    data[DataTable.match_status] = global_data[DataTable.match_status]

    data = data.loc[data[MatchInformationTable.updated_match_status].isin(last_updated_status_list)]
    data = data.loc[data[DataTable.match_status].isin(status_list)]
    if only_new:
        data = data.loc[data[UpdatableTable.updated_time] == -1.0]
    data = data.loc[(global_data[DataTable.match_status] != 0) | (global_data[DataTable.match_time] < break_time)]
    data.sort_values(
        by=[DataTable.match_status, MatchInformationTable.updated_time], ascending=[False, True], inplace=True
    )

    if limit_count is not None:
        data = data.iloc[:limit_count]

    if debug:
        save_to_csv(data, project_path, 'processing')

    data_analysis = pd.DataFrame(columns=['数量'])
    data_analysis.loc['全部'] = len(data)
    data_analysis.loc['从未获取'] = len(data.loc[data[UpdatableTable.updated_time] == -1.0])
    for status in data[DataTable.match_status].unique():
        data_analysis.loc[match_status_dict[status]] = len(data.loc[data[DataTable.match_status] == status])

    rprint()

    rprint('处理数据分析：')
    Console().print(Markdown(data_analysis.to_markdown()))

    rprint()

    rprint(f'本次更新将采取基准更新间隔 [bold blue]{interval}[/bold blue] 秒，', end='')
    rprint(f'额外更新间隔 [bold blue]{extra_interval}[/bold blue] 秒，', end='')
    rprint(f'使用额外更新间隔的概率 [bold blue]{extra_interval_probability}[/bold blue]，', end='')
    rprint(f'更新间隔偏移量范围 [bold blue]{interval_offset_range}[/bold blue] 秒，', end='')
    if len(last_updated_status_list) > 0:
        status_text_list = [match_status_dict[status] for status in list(set(last_updated_status_list) - {-1})]
        rprint(f'只更新上次更新时状态为 [bold yellow]{status_text_list}[/bold yellow] 的比赛，', end='')
    else:
        rprint('不对上次更新时比赛状态进行限制，', end='')
    if len(status_list) > 0:
        status_text_list = [match_status_dict[status] for status in status_list]
        rprint(f'只更新状态为 [bold yellow]{status_text_list}[/bold yellow] 的比赛，', end='')
    else:
        rprint('不对比赛状态进行限制，', end='')
    if 0 in status_list and break_hours > 0:
        rprint(f'跳过 [bold blue]{break_hours}[/bold blue] 小时后的未开始的比赛，', end='')
    elif 0 in status_list and break_hours == 0:
        rprint('不跳过未开始的比赛，', end='')
    else:
        rprint('未开始的比赛不在更新列表中，跳过未开始比赛的选项将被忽略，', end='')
    if only_new:
        rprint(f'[bold yellow]只更新从未获取过的比赛[/bold yellow]，', end='')
    else:
        rprint('不对比赛是否已获取过进行限制，', end='')
    if limit_count is not None:
        rprint(f'只更新 [bold yellow]{limit_count}[/bold yellow] 场比赛')
    else:
        rprint('不对更新数量进行限制')

    rprint()

    rprint(f'开始更新{action.name}信息...')

    ua = UserAgent().random

    interval_list: list[Interval] = []
    extra_interval_count = 0
    for i in range(len(data) - 1):
        delta = random.randint(-interval_offset_range, interval_offset_range)
        if random.random() < extra_interval_probability:
            interval_list.append(Interval(extra_interval + delta, True))
            extra_interval_count += 1
        else:
            interval_list.append(Interval(interval + delta, False))

    def get_eta(progress: int) -> timedelta:
        return timedelta(seconds=sum([_i.seconds for _i in interval_list]) + (len(data) - progress) * 2)

    initial_eta = get_eta(0)

    rprint(f'本次更新将使用 {extra_interval_count} 次额外更新间隔')

    start_time = datetime.now()

    with typer.progressbar(data.index, show_eta=False, show_percent=True, show_pos=True) as indexes:
        eta = initial_eta
        for index, match_id in enumerate(indexes):
            rprint(f'   预计全部更新还需要 {eta}')

            host_name = team_data.loc[global_data.loc[match_id, DataTable.host_id], TeamTable.name]
            guest_name = team_data.loc[global_data.loc[match_id, DataTable.guest_id], TeamTable.name]
            status = f'[bold blue]{match_status_dict[global_data.loc[match_id, DataTable.match_status]]}[/bold blue]'

            rprint(f'正在更新代号为 {match_id} 的比赛（{host_name} VS {guest_name}，{status}）的{action.name}信息...')

            if data.loc[match_id, MatchInformationTable.updated_time] == -1.0:
                rprint(f'该场比赛为从未获取过{action.name}的比赛')

            before, after = action.update(match_id=match_id, global_data=global_data, team_data=team_data, ua=ua)

            if before == after:
                rprint(f'该场比赛的{action.name}信息未发生变化')
                rprint('当前：')
            else:
                rprint(f'该场比赛的{action.name}信息已更新')
                rprint('更新前：')
                rprint(f'[red]{before}')
                rprint('更新后：')
            rprint(f'[bold blue]{after}')

            if index == len(data) - 1:
                break

            current_interval = interval_list[0]
            if current_interval.extra:
                rprint('[yellow]将使用额外更新间隔，请耐心等待')
            sleep(current_interval.seconds)
            interval_list.pop(0)
            eta = get_eta(index + 1)

            if random_ua:
                ua = UserAgent().random

    used_time = datetime.now() - start_time
    rprint(f'更新完成，用时 {used_time}，', end='')
    if used_time > initial_eta:
        rprint(f'[yellow]超出[/yellow]预计时间 {used_time - initial_eta}')
    elif used_time < initial_eta:
        rprint(f'[blue]少于[/blue]预计时间 {initial_eta - used_time}')
    else:
        rprint('[bold green]正巧与预计时间相等')
