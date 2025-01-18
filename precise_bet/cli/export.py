#  Copyright (C) 2025  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import inspect
import re
from abc import ABC
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer
from openpyxl.worksheet.worksheet import Worksheet
from rich.prompt import Confirm

from precise_bet import rprint, stdout_console
from precise_bet.data import save_message, save_to_csv, save_to_html
from precise_bet.type import (
    AverageEuropeOddTable,
    DataTable,
    HandicapTable,
    LeagueTable,
    RecentResultsTable,
    ScoreTable,
    ValueTable,
    match_status_dict,
)
from precise_bet.type.table import SpTable
from precise_bet.util import can_write, mkdir

red = "color: #FF0000;"
handicapped_point_color = "color: #2F75B5;"
half_score_color = "color: #00B050;"
result_color = "color: #FF8080;"
handicap_background_color = "background-color: #E1E9F0;"
odd_background_color = "background-color: #F4B084;"
ya_hei = "font-family: 微软雅黑;"
# noinspection SpellCheckingInspection
calibri = "font-family: Calibri;"
tahoma = "font-family: Tahoma;"
nine_point = "font-size: 9pt;"
ten_point = "font-size: 10pt;"
bold = "font-weight: bold;"
center = "text-align: center;"
left = "text-align: left;"
middle = "vertical-align: middle;"


class ExportFileFormat(ABC):
    extension: str

    def __hash__(self):
        return hash(self.__class__)

    def __eq__(self, other):
        if inspect.isclass(other):
            return issubclass(other, self.__class__) or issubclass(
                self.__class__, other
            )
        return super().__eq__(other)


class TextBasedFormat(ExportFileFormat, ABC):
    pass


class Csv(TextBasedFormat):
    extension = ".csv"


class StyledFormat(ExportFileFormat, ABC):
    pass


class Html(StyledFormat):
    extension = ".html"


class Excel(StyledFormat):
    extension = ".xlsx"


class Special(Excel):
    pass


class ExportFileFormats(Enum):
    csv = Csv()
    html = Html()
    excel = Excel()
    special = Special()


def formats_parser(value: str | ExportFileFormat) -> ExportFileFormat:
    if isinstance(value, ExportFileFormat):
        return value
    try:
        return ExportFileFormats[value].value
    except KeyError:
        raise typer.BadParameter(f"不支持的文件格式：{value}")


def export(
    ctx: typer.Context,
    file_name: Annotated[
        str, typer.Option("--file-name", "-n", help="导出文件名")
    ] = "exported/data",
    file_name_suffix: Annotated[
        Optional[str], typer.Option("--file-name-suffix", "-s", help="导出文件名后缀")
    ] = None,
    file_format: Annotated[
        ExportFileFormat,
        typer.Option(
            "--file-format",
            "-f",
            help="导出文件格式",
            prompt="请输入文件格式",
            parser=formats_parser,
        ),
    ] = ExportFileFormats.csv.value,
    volume_number: Annotated[
        Optional[int], typer.Option("--volume-number", "-v", help="期号")
    ] = None,
    match_number_range: Annotated[
        Optional[str],
        typer.Option("--match-number-range", "-r", help="场次范围（如 1-3）"),
    ] = None,
):
    """导出数据"""

    project_path: Path = ctx.obj["project_path"]

    if file_name_suffix:
        file_name += file_name_suffix

    save_path = project_path / f"{file_name}{file_format.extension}"
    mkdir(save_path.parent)

    if not can_write(save_path) and not Confirm.ask(
        f"文件 [bold]{save_path}[/bold] 当前不可写入，是否继续？",
        console=stdout_console,
        default=False,
    ):
        alternative: Path
        for i in range(1, 100):
            alternative = project_path / f"{file_name}{i}{file_format.extension}"
            if can_write(alternative):
                if Confirm.ask(
                    f"是否保存到 [bold]{alternative}[/bold] ？",
                    console=stdout_console,
                    default=True,
                ):
                    save_path = alternative
                    break
                else:
                    rprint("已取消")
                    return

    rprint("开始导出数据...")

    rprint("正在处理数据...")

    data = DataTable(project_path).read()
    score = ScoreTable(project_path).read()
    value = ValueTable(project_path).read()
    league = LeagueTable(project_path).read()
    handicap = HandicapTable(project_path).read()
    recent_results = RecentResultsTable(project_path).read()
    sp = SpTable(project_path).read()
    odd = AverageEuropeOddTable(project_path).read()

    if volume_number:
        rprint(f"已指定期号为 [bold]{volume_number}[/bold]")
        data = data[data[DataTable.volume_number] == volume_number]

    if volume_number and match_number_range:
        start, end = map(int, match_number_range.split("-"))
        rprint(f"已指定场次范围为 [bold]{start}[/bold] 至 [bold]{end}[/bold]")
        data = data[
            (data[DataTable.match_number] >= start)
            & (data[DataTable.match_number] <= end)
        ]

    def calculate_match_result(score_text: str):
        score_list = score_text.split("-")
        host_score = int(score_list[0].strip())
        guest_score = int(score_list[1].strip())
        if host_score > guest_score:
            return "胜"
        elif host_score == guest_score:
            return "平"
        else:
            return "负"

    def calculate_result_with_concede(row: pd.Series):
        score_list = row["比分"].split("-")
        host_score = int(score_list[0].strip())
        guest_score = int(score_list[1].strip())
        concede_point = 0
        concede_match = re.match(r".*\(([+-][\d.]+)\)", row[DataTable.host_name])
        if concede_match:
            concede_point = int(concede_match.group(1))
        if host_score + concede_point > guest_score:
            return "胜"
        elif host_score + concede_point == guest_score:
            return "平"
        else:
            return "负"

    rprint(f"正在整合数据{'并添加样式' if file_format == StyledFormat else ''}...")

    if file_format != Special:
        handicap_name = data[DataTable.handicap_name]
        data.drop(columns=[DataTable.handicap_name], inplace=True)

    # '+' 为特殊运算符，表示合并，不可替换为模板字符串
    score_str = (
        score[ScoreTable.host_score].astype(str)
        + " - "
        + score[ScoreTable.guest_score].astype(str)
    )
    data.insert(data.columns.get_loc(DataTable.guest_name), "比分", score_str)
    data[AverageEuropeOddTable.class_columns()] = odd[
        AverageEuropeOddTable.class_columns()
    ]
    data["结果"] = data["比分"].apply(calculate_match_result)
    placeholder = "-" if file_format == TextBasedFormat else ""
    data[SpTable.class_columns()] = sp[SpTable.class_columns()]
    data["让球结果"] = data.apply(calculate_result_with_concede, axis=1)
    data.loc[data[DataTable.match_status] != 4, ["比分", "结果", "让球结果"]] = (
        placeholder
    )
    data[ValueTable.class_columns()] = value[ValueTable.class_columns()]
    if file_format != Special:
        # noinspection PyUnboundLocalVariable
        data[DataTable.handicap_name] = handicap_name
    data[HandicapTable.class_columns()[:3]] = handicap[
        HandicapTable.class_columns()[:3]
    ]
    data[HandicapTable.class_columns()[3:]] = handicap[
        HandicapTable.class_columns()[3:]
    ]

    timezone = datetime.now().astimezone().tzinfo
    data[DataTable.match_time] = pd.to_datetime(
        data[DataTable.match_time], unit="s", utc=True
    ).dt.tz_convert(timezone)
    data.drop(columns=[DataTable.host_id, DataTable.guest_id], inplace=True)

    if file_format == Special:
        for column in ValueTable.class_columns():
            data[column] = data[column].apply(lambda x: 0 if pd.isna(x) else x)
        for column in HandicapTable.class_columns():
            data[column] = data[column].apply(lambda x: 0.0 if pd.isna(x) else x)

    if file_format == Special:
        data["全场比分"] = data["比分"]

    half_score = data[DataTable.half_score]
    if file_format == StyledFormat:
        half_score = half_score.apply(lambda x: "" if x == "-" else x)
    if file_format == Special:
        data.drop(columns=[DataTable.half_score], inplace=True)
    data[DataTable.half_score] = half_score

    if file_format == Special:
        handicap_name = data[DataTable.handicap_name]
        data.drop(columns=[DataTable.handicap_name], inplace=True)
        data[DataTable.handicap_name] = handicap_name

    status = data[DataTable.match_status].map(match_status_dict)
    if file_format == Special:
        data.drop(columns=[DataTable.match_status], inplace=True)
    data[DataTable.match_status] = status

    if file_format == Csv:
        data[DataTable.league_id] = data[DataTable.league_id].map(
            league[LeagueTable.name]
        )
        save_to_csv(data, project_path, file_name, file_format.extension)
    elif file_format == StyledFormat:
        data[DataTable.match_time] = data[DataTable.match_time].dt.tz_localize(None)
        league_styles = data[DataTable.league_id].map(league[LeagueTable.color])
        league_styles = league_styles.apply(
            lambda x: f"color: white;background-color: {x};"
            f"{ya_hei}{nine_point}{center}{middle}"
        )
        data[DataTable.league_id] = data[DataTable.league_id].map(
            league[LeagueTable.name]
        )

        host_style = []
        guest_style = []

        def append_team_style(name: str, style_list: list):
            team_color = ""
            if file_format == Special:
                if "(+1)" in name:
                    team_color = handicapped_point_color
                elif "(-1)" in name:
                    team_color = red
            style_list.append(f"{team_color}{ten_point}{middle}")

        for match_id in data.index:
            host = data.loc[match_id, DataTable.host_name]
            guest = data.loc[match_id, DataTable.guest_name]
            append_team_style(host, host_style)
            append_team_style(guest, guest_style)

        handicap_style = []
        for match_id in data.index:
            color = ""
            if data.loc[match_id, HandicapTable.live_average_handicap] < 0:
                color = handicap_background_color
            elif data.loc[match_id, HandicapTable.live_average_handicap] == 0:
                if data.loc[match_id, HandicapTable.early_average_handicap] < 0:
                    color = handicap_background_color
                elif data.loc[match_id, HandicapTable.early_average_handicap] == 0:
                    if (
                        data.loc[match_id, ValueTable.guest_value]
                        <= data.loc[match_id, ValueTable.host_value]
                    ):
                        color = handicap_background_color
            handicap_style.append(f"{color}{tahoma}{nine_point}{center}{middle}")

        odd_style = f"{calibri}{ten_point}{center}{middle}"
        sp_win_style = [
            (odd_background_color if r == "胜" else "") + odd_style
            for r in data["让球结果"]
        ]
        sp_draw_style = [
            (odd_background_color if r == "平" else "") + odd_style
            for r in data["让球结果"]
        ]
        sp_lose_style = [
            (odd_background_color if r == "负" else "") + odd_style
            for r in data["让球结果"]
        ]
        europe_win_style = [
            (odd_background_color if r == "胜" else "") + odd_style
            for r in data["结果"]
        ]
        europe_draw_style = [
            (odd_background_color if r == "平" else "") + odd_style
            for r in data["结果"]
        ]
        europe_lose_style = [
            (odd_background_color if r == "负" else "") + odd_style
            for r in data["结果"]
        ]

        length = len(data)
        style = data.style
        style.apply(
            lambda _: [f"{ya_hei}{nine_point}{center}{middle}"] * length,
            subset=[DataTable.volume_number, DataTable.match_number],
        )
        style.apply(lambda _: league_styles, subset=[DataTable.league_id])
        style.apply(
            lambda _: [f"{nine_point}{left}{middle}"] * length,
            subset=[DataTable.round_number],
        )
        style.apply(
            lambda _: [f"{calibri}{nine_point}{left}{middle}"] * length,
            subset=[DataTable.match_time],
        )
        style.apply(lambda _: host_style, subset=[DataTable.host_name])
        style.apply(lambda _: guest_style, subset=[DataTable.guest_name])
        style.apply(
            lambda _: [f"{ya_hei}{nine_point}{left}{middle}"] * length,
            subset=[DataTable.handicap_name],
        )
        style.apply(
            lambda _: [f"{calibri}{red}{ten_point}{center}{middle}"] * length,
            subset=["比分"],
        )
        style.apply(
            lambda _: [f"{calibri}{half_score_color}{ten_point}{center}{middle}"]
            * length,
            subset=[DataTable.half_score],
        )
        style.apply(
            lambda _: [f"{ya_hei}{result_color}{nine_point}{center}{middle}"] * length,
            subset=["结果", "让球结果"],
        )
        style.apply(lambda _: sp_win_style, subset=[SpTable.win])
        style.apply(lambda _: sp_draw_style, subset=[SpTable.draw])
        style.apply(lambda _: sp_lose_style, subset=[SpTable.lose])
        style.apply(lambda _: europe_win_style, subset=[AverageEuropeOddTable.win])
        style.apply(lambda _: europe_draw_style, subset=[AverageEuropeOddTable.draw])
        style.apply(lambda _: europe_lose_style, subset=[AverageEuropeOddTable.lose])
        style.apply(
            lambda _: [f"{left}{middle}"] * length, subset=ValueTable.class_columns()
        )
        style.apply(lambda _: handicap_style, subset=HandicapTable.class_columns())
        if file_format == Special:
            style.apply(
                lambda _: [f"{calibri}{red}{ten_point}{center}{middle}"] * length,
                subset=["全场比分"],
            )
            style.data[DataTable.match_number] = (
                style.data[DataTable.match_number].astype(str).str.zfill(3)
            )

        if file_format == Html:
            save_to_html(style, project_path, file_name, file_format.extension)
            return

        exported_time = datetime.now().strftime("%Y%m%d-%H%M%S")

        def calculate_column_name(index: int):
            if index < 26:
                return chr(ord("A") + index)
            return calculate_column_name(index // 26 - 1) + chr(ord("A") + index % 26)

        columns = {
            column: calculate_column_name(index + 1)
            for index, column in enumerate(style.data.columns.values)
        }

        writer = pd.ExcelWriter(save_path)

        style.to_excel(writer, sheet_name=exported_time)

        worksheet: Worksheet = writer.sheets[exported_time]

        for cell in worksheet[columns[DataTable.match_time]]:
            cell.number_format = "yyyy/m/d h:mm"

        for cells in (
            worksheet[
                f"{columns[AverageEuropeOddTable.win]}:{columns[AverageEuropeOddTable.lose]}"
            ]
            + worksheet[f"{columns[SpTable.win]}:{columns[SpTable.lose]}"]
        ):
            for cell in cells:
                cell.number_format = "0.00"

        handicap_start = columns[HandicapTable.live_average_water1]
        handicap_end = columns[HandicapTable.early_average_water2]

        for cells in worksheet[f"{handicap_start}:{handicap_end}"]:
            for cell in cells:
                cell.number_format = "0.000"

        worksheet.column_dimensions[columns[DataTable.match_time]].width = 15

        worksheet.column_dimensions[columns[DataTable.host_name]].width = 20
        worksheet.column_dimensions[columns[DataTable.guest_name]].width = 20

        worksheet.column_dimensions[columns[DataTable.handicap_name]].width = 10

        worksheet.column_dimensions[columns["结果"]].width = 2
        worksheet.column_dimensions[columns["让球结果"]].width = 2

        for column in [columns["比分"], columns[DataTable.half_score]]:
            worksheet.column_dimensions[column].width = 4

        if file_format == Special:
            worksheet.column_dimensions[columns["全场比分"]].width = 4

        for i in range(3):
            worksheet.column_dimensions[chr(ord(columns[SpTable.win]) + i)].width = 6

        for i in range(3):
            worksheet.column_dimensions[
                chr(ord(columns[AverageEuropeOddTable.win]) + i)
            ].width = 6

        for i in range(6 if file_format == Special else 8):
            worksheet.column_dimensions[chr(ord(handicap_start) + i)].width = 6

        if file_format == Special:
            finished_indexes = data.index[
                data[DataTable.match_status] == match_status_dict[4]
            ]
            if len(finished_indexes) > 0:
                index = data.index.get_loc(finished_indexes[-1])
            else:
                index = 0
            active_cell = f"A{index + 3}"
            rprint(f"正在设置活动单元格：[bold]{active_cell}[/bold] ...")
            # noinspection PyPep8Naming
            worksheet.views.sheetView[0].topLeftCell = active_cell
            for selection in worksheet.views.sheetView[0].selection:
                selection.activeCell = active_cell
                # noinspection SpellCheckingInspection
                selection.sqref = active_cell

        save_message(save_path, lambda: writer.close())
