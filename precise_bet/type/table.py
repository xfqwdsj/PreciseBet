#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from abc import ABC
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd
# noinspection PyProtectedMember
from pandas._typing import Dtype

match_status_dict = {
    -2: '从旧数据导入', -1: '无', 0: '未开始', 1: '上半场', 2: '中场', 3: '下半场', 4: '已结束', 5: '取消', 6: '改期',
    7: '腰斩', 8: '中断', 9: '待定', 10: '加时赛开始', 11: '加时赛结束', 12: '点球'
}


class ColumnOrder(Enum):
    index = 0
    name = 1
    content = 2
    updated_time = 3
    match_information = 4


@dataclass
class Column:
    name: str
    type: Dtype
    order: ColumnOrder = ColumnOrder.content

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)


class Row(dict[Column, Any]):
    pass


class UpdatableRow(Row):
    def append_updated_time(self):
        self.update({UpdatableTable.updated_time: datetime.now().timestamp()})
        return self


class Table(pd.DataFrame, ABC):
    name_: str
    index_: Column

    _table_pairs: OrderedDict[str, Column] | None = None

    @classmethod
    def class_pairs(cls) -> dict[str, Column]:
        return {i: vars(cls)[i] for i in vars(cls) if not i.endswith('_') and isinstance(vars(cls)[i], Column)}

    @classmethod
    def class_columns(cls) -> list[Column]:
        return list(cls.class_pairs().values())

    @classmethod
    def table_pairs(cls) -> OrderedDict[str, Column]:
        if cls._table_pairs is None:
            mro = [i for i in cls.__mro__ if issubclass(i, Table)]
            result = OrderedDict[str, Column]()
            for cls_ in mro:
                result.update(cls_.class_pairs())
            cls._table_pairs = OrderedDict[str, Column](sorted(result.items(), key=lambda x: x[1].order.value))
        return cls._table_pairs

    @classmethod
    def table_columns(cls) -> list[Column]:
        return list(cls.table_pairs().values())

    @classmethod
    def column_names(cls) -> list[str]:
        return [column.name for column in cls.table_columns()]

    @classmethod
    def column_types(cls) -> dict[str, Dtype]:
        return {column.name: column.type for column in cls.table_columns()}

    @classmethod
    def generate_row(cls, **kwargs) -> Row:
        p = cls.table_pairs()
        result = Row()
        for column in kwargs:
            if column in p:
                result[p[column]] = kwargs[column]
            else:
                raise KeyError(f'在生成一行时，未找到名为 {column} 的列')
        return result

    def update_row(self, row_id: Any, row: Row):
        for column in row:
            if column not in self:
                raise KeyError(f'在更新一行时，未找到名为 {column} 的列')
            self.loc[row_id, column] = row[column]

    def create(self):
        super().__init__(
            pd.DataFrame({column: pd.Series(dtype=column.type) for column in self.table_columns()}).set_index(
                self.index_
            )
        )
        return self

    def read_from_file(self, file: Path):
        table = self.create()
        data = pd.read_csv(file, dtype=self.column_types()).set_index(self.index_.name)
        for column in self.table_columns():
            if column.name in data:
                table[column] = data[column.name]
        super().__init__(table)
        return self

    def read_from_dir(self, path: Path):
        return self.read_from_file(path / f'{self.name_}.csv')

    def read_from_dir_or_create(self, path: Path):
        if (path / f'{self.name_}.csv').exists():
            return self.read_from_dir(path)
        else:
            return self.create()

    def save_to_file(self, file: Path):
        from precise_bet.data import save

        save(self, file, lambda d, p: d.to_csv(p))

    def save_to_dir(self, path: Path):
        self.save_to_file(path / f'{self.name_}.csv')


class ProjectTable(Table, ABC):
    project_path: Path

    def __init__(self, project_path: Path):
        super().__init__()
        self.project_path = project_path

    def read(self):
        return self.read_from_dir(self.project_path)

    def read_or_create(self):
        return self.read_from_dir_or_create(self.project_path)

    def save(self):
        self.save_to_dir(self.project_path)


# class VolumeTable(ProjectTable, ABC):
#     volume_number: int
#
#     def __init__(self, project_path: Path, volume_number: int):
#         super().__init__(project_path)
#         self.volume_number = volume_number
#
#     def read(self):
#         return self.read_from_dir(self.project_path / str(self.volume_number))
#
#     def read_or_create(self):
#         return self.read_from_dir_or_create(self.project_path / str(self.volume_number))
#
#     def save(self):
#         self.save_to_dir(self.project_path / str(self.volume_number))


class MatchTable(ProjectTable, ABC):
    match_id = Column('代号', str, ColumnOrder.index)

    index_ = match_id

    def get_row(self, match_id: str):
        return self.data.loc[match_id]

    def get_cells(self, match_id: str, *columns: Column):
        return self.data.loc[match_id, columns]


class DataTable(MatchTable):
    name_ = 'data'

    volume_number = Column('期号', int)
    match_number = Column('场次', int)
    league_id = Column('赛事', str)
    round_number = Column('轮次', str)
    match_time = Column('比赛时间', int)
    match_status = Column('状态', int)
    host_id = Column('主队', int)
    host_name = Column('主队名称', str)
    guest_id = Column('客队', int)
    guest_name = Column('客队名称', str)
    half_score = Column('半场比分', str)
    handicap_name = Column('盘口', str)


class UpdatableTable(Table, ABC):
    updated_time = Column('更新时间', float, ColumnOrder.updated_time)

    @classmethod
    def generate_row(cls, **kwargs) -> UpdatableRow:
        return UpdatableRow(super().generate_row(**kwargs))


class MatchInformationTable(MatchTable, UpdatableTable, ABC):
    updated_match_status = Column('更新时比赛状态', int, ColumnOrder.match_information)


class ScoreTable(MatchInformationTable):
    name_ = 'score'

    host_score = Column('主队', int)
    guest_score = Column('客队', int)


class ValueTable(MatchInformationTable):
    name_ = 'value'

    host_value = Column('主队价值', pd.UInt32Dtype())
    guest_value = Column('客队价值', pd.UInt32Dtype())

    def get_data(self, match_id: MatchTable.match_id.type) -> list[int]:
        return list(self.loc[match_id, self.class_columns()])

    @classmethod
    def empty_row(cls):
        return cls.generate_row(host_value=None, guest_value=None, updated_time=-1.0, updated_match_status=-1)

    @classmethod
    def row_from_list(cls, value: list[int], updated_match_status: int):
        return cls.generate_row(
            host_value=value[0], guest_value=value[1], updated_match_status=updated_match_status
        ).append_updated_time()

    def update_from_list(self, match_id: MatchTable.match_id.type, value: list[int], updated_match_status: int):
        self.update_row(match_id, self.row_from_list(value, updated_match_status))

    def get_team_id(self, match_id: MatchTable.match_id.type, column: Column) -> int:
        if column == DataTable.host_id or column == self.host_value:
            return self.loc[match_id, self.host_value]
        elif column == DataTable.guest_id or column == self.guest_value:
            return self.loc[match_id, self.guest_value]
        else:
            raise KeyError(f'在获取球队代号时，未找到名为 {column.name} 的列')


class HandicapTable(MatchInformationTable):
    name_ = 'handicap'

    live_average_water1 = Column('平即水1', pd.Float32Dtype())
    live_average_handicap = Column('平即盘', pd.Float32Dtype())
    live_average_water2 = Column('平即水2', pd.Float32Dtype())
    early_average_water1 = Column('平初水1', pd.Float32Dtype())
    early_average_handicap = Column('平初盘', pd.Float32Dtype())
    early_average_water2 = Column('平初水2', pd.Float32Dtype())

    def get_data(self, match_id: MatchTable.match_id.type) -> list[float]:
        return list(self.loc[match_id, self.class_columns()])

    @classmethod
    def empty_row(cls):
        return cls.generate_row(
            live_average_water1=None, live_average_handicap=None, live_average_water2=None, early_average_water1=None,
            early_average_handicap=None, early_average_water2=None, updated_time=-1.0, updated_match_status=-1
        )

    @classmethod
    def row_from_list(cls, handicap: list[float], updated_match_status: int):
        return cls.generate_row(
            live_average_water1=handicap[0], live_average_handicap=handicap[1], live_average_water2=handicap[2],
            early_average_water1=handicap[3], early_average_handicap=handicap[4], early_average_water2=handicap[5],
            updated_match_status=updated_match_status
        ).append_updated_time()

    def update_from_list(self, match_id: MatchTable.match_id.type, handicap: list[float], updated_match_status: int):
        self.update_row(match_id, self.row_from_list(handicap, updated_match_status))


class OddTable(MatchInformationTable):
    name_ = 'odd'

    win = Column('胜', float)
    draw = Column('平', float)
    lose = Column('负', float)

    @classmethod
    def row_from_list(cls, odds: list[float], updated_time: float, updated_match_status: int):
        return cls.generate_row(
            win=odds[0], draw=odds[1], lose=odds[2], updated_time=updated_time,
            updated_match_status=updated_match_status
        )


class NamedTable(Table, ABC):
    name = Column('名称', str, ColumnOrder.name)


class LeagueTable(ProjectTable, NamedTable):
    name_ = 'league'

    league_id = Column('代号', str, ColumnOrder.index)
    color = Column('颜色', str)
    type = Column('类型', pd.CategoricalDtype(categories=['league', 'cup', 'unknown']))

    index_ = league_id

    @classmethod
    def empty_row(cls, name: str, color: str):
        return cls.generate_row(name=name, color=color, type='unknown')

    def update_name_and_color(self, league_id: str, name: str, color: str):
        self.loc[league_id, LeagueTable.name] = name
        self.loc[league_id, LeagueTable.color] = color

    def update_type(self, league_id: str, league_type: str):
        self.loc[league_id, LeagueTable.type] = league_type


class TeamTable(ProjectTable, NamedTable, UpdatableTable):
    name_ = 'team'

    team_id = Column('代号', int)
    value = Column('价值', pd.UInt32Dtype())

    index_ = team_id

    @classmethod
    def empty_row(cls, name: str):
        return cls.generate_row(name=name, value=None, updated_time=-1.0)

    @classmethod
    def row_from_value(cls, value: int):
        return cls.generate_row(value=value).append_updated_time()

    def update_from_value(self, team_id: int, value: int):
        self.update_row(team_id, self.row_from_value(value))
