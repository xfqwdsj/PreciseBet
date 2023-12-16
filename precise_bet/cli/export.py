#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from datetime import datetime
from pathlib import Path

import click
import pandas as pd
from click_option_group import optgroup

from precise_bet.data import save_message, save_to_csv
from precise_bet.type import DataTable, HandicapTable, LeagueTable, OddTable, ScoreTable, ValueTable, match_status_dict
from precise_bet.util import mkdir

red = 'color: #FF0000;'
handicapped_point_color = 'color: #2F75B5;'
half_score_color = 'color: #00B050;'
result_color = 'color: #FF8080;'
handicap_background_color = 'background-color: #E1E9F0;'
handicap_highlight_color = 'background-color: #D7327D;'
odd_background_color = 'background-color: #F4B084;'
ya_hei = 'font-family: 微软雅黑;'
calibri = 'font-family: Calibri;'
tahoma = 'font-family: Tahoma;'
nine_point = 'font-size: 9pt;'
ten_point = 'font-size: 10pt;'
center = 'text-align: center;'
left = 'text-align: left;'
middle = 'vertical-align: middle;'


def is_excel(file_format: str):
    return file_format == 'excel' or file_format == 'special'


@click.command()
@click.pass_context
@optgroup.group('导出选项', help='指定导出时使用的选项')
@optgroup.option('--file-name', '-n', help='导出文件名', default='exported/data', type=str)
@optgroup.option(
    '--file-format', '-f', help='导出文件格式', prompt='请输入文件格式', default='csv',
    type=click.Choice(['csv', 'excel', 'special'])
)
def export(ctx, file_name: str, file_format: str):
    """
    导出数据
    """

    project_path: Path = ctx.obj['project_path']

    click.echo('开始导出数据...')

    click.echo(f'正在处理数据...')

    data = DataTable(project_path).read()
    score = ScoreTable(project_path).read()
    value = ValueTable(project_path).read()
    league = LeagueTable(project_path).read()
    handicap = HandicapTable(project_path).read()
    odd = OddTable(project_path).read()

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

    if not file_format == 'special':
        handicap_name = data[DataTable.handicap_name]
        data.drop(columns=[DataTable.handicap_name], inplace=True)

    # '+' 为特殊运算符，表示合并，不可替换为模板字符串
    score_str = score[ScoreTable.host_score].astype(str) + ' - ' + score[ScoreTable.guest_score].astype(str)
    data.insert(8, '比分', score_str)
    data[OddTable.class_columns()] = odd[OddTable.class_columns()]
    data['结果'] = data['比分'].apply(calculate_result)
    placeholder = '-' if file_format == 'csv' else ''
    data.loc[data[DataTable.match_status] != 4, ['比分', '结果']] = placeholder
    data[ValueTable.class_columns()] = value[ValueTable.class_columns()]
    if not file_format == 'special':
        # noinspection PyUnboundLocalVariable
        data[DataTable.handicap_name] = handicap_name
    data[HandicapTable.class_columns()[:3]] = handicap[HandicapTable.class_columns()[:3]]
    if file_format == 'special':
        data['空列1'] = ''
        data['空列2'] = ''
    data[HandicapTable.class_columns()[3:]] = handicap[HandicapTable.class_columns()[3:]]

    click.echo(f'正在整合数据{'并添加样式' if is_excel(file_format) else ''}...')

    timezone = datetime.now().astimezone().tzinfo

    data[DataTable.match_time] = pd.to_datetime(data[DataTable.match_time], unit='s', utc=True).dt.tz_convert(timezone)
    data.drop(columns=[DataTable.host_id, DataTable.guest_id], inplace=True)

    if file_format == 'special':
        data['全场比分'] = data['比分']

    half_score = data[DataTable.half_score]
    if is_excel(file_format):
        half_score = half_score.apply(lambda x: '' if x == '-' else x)
    if file_format == 'special':
        data.drop(columns=[DataTable.half_score], inplace=True)
    data[DataTable.half_score] = half_score

    if file_format == 'special':
        handicap_name = data[DataTable.handicap_name]
        data.drop(columns=[DataTable.handicap_name], inplace=True)
        data[DataTable.handicap_name] = handicap_name

    status = data[DataTable.match_status].map(match_status_dict)
    if file_format == 'special':
        data.drop(columns=[DataTable.match_status], inplace=True)
    data[DataTable.match_status] = status

    if file_format == 'csv':
        data[DataTable.league_id] = data[DataTable.league_id].map(league[LeagueTable.name])
        save_to_csv(data, project_path, file_name)
    elif is_excel(file_format):
        data[DataTable.match_time] = data[DataTable.match_time].dt.tz_localize(None)
        league_styles = data[DataTable.league_id].map(league[LeagueTable.color])
        league_styles = league_styles.apply(
            lambda x: f'color: white;background-color: {x};'
                      f'{ya_hei}{nine_point}{center}{middle}'
        )
        data[DataTable.league_id] = data[DataTable.league_id].map(league[LeagueTable.name])

        host_style = []
        guest_style = []

        def append_team_style(name: str, style_list: list):
            team_color = ''
            if file_format == 'special':
                if '(+1)' in name:
                    team_color = handicapped_point_color
                elif '(-1)' in name:
                    team_color = red
            style_list.append(f'{team_color}{ten_point}{middle}')

        for match_id in data.index:
            host = data.loc[match_id, DataTable.host_name]
            guest = data.loc[match_id, DataTable.guest_name]
            append_team_style(host, host_style)
            append_team_style(guest, guest_style)

        handicap_style = []
        if file_format == 'special':
            empty_column_style = []
        for match_id in data.index:
            color = ''
            if data.loc[match_id, HandicapTable.live_average_handicap] > 0:
                color = handicap_highlight_color
            elif data.loc[match_id, HandicapTable.live_average_handicap] == 0:
                if data.loc[match_id, HandicapTable.early_average_handicap] > 0:
                    color = handicap_highlight_color
            if file_format == 'special':
                # noinspection PyUnboundLocalVariable
                empty_column_style.append(color)
            if color == '':
                color = handicap_background_color
            handicap_style.append(f'{color}{tahoma}{nine_point}{center}{middle}')

        odd_style = f'{calibri}{ten_point}{center}{middle}'
        win_style = [(odd_background_color if r == '胜' else '') + odd_style for r in data['结果']]
        draw_style = [(odd_background_color if r == '平' else '') + odd_style for r in data['结果']]
        lose_style = [(odd_background_color if r == '负' else '') + odd_style for r in data['结果']]

        length = len(data)
        style = data.style
        style.apply(
            lambda _: [f'{ya_hei}{nine_point}{center}{middle}'] * length,
            subset=[DataTable.volume_number, DataTable.match_number]
        )
        style.apply(lambda _: league_styles, subset=[DataTable.league_id])
        style.apply(lambda _: [f'{nine_point}{left}{middle}'] * length, subset=[DataTable.round_number])
        style.apply(lambda _: [f'{calibri}{nine_point}{left}{middle}'] * length, subset=[DataTable.match_time])
        style.apply(lambda _: host_style, subset=[DataTable.host_name])
        style.apply(lambda _: guest_style, subset=[DataTable.guest_name])
        style.apply(lambda _: [f'{ya_hei}{nine_point}{left}{middle}'] * length, subset=[DataTable.handicap_name])
        style.apply(lambda _: [f'{calibri}{red}{ten_point}{center}{middle}'] * length, subset=['比分'])
        style.apply(
            lambda _: [f'{calibri}{half_score_color}{ten_point}{center}{middle}'] * length,
            subset=[DataTable.half_score]
        )
        style.apply(lambda _: [f'{ya_hei}{result_color}{nine_point}{center}{middle}'] * length, subset=['结果'])
        style.apply(lambda _: win_style, subset=[OddTable.win])
        style.apply(lambda _: draw_style, subset=[OddTable.draw])
        style.apply(lambda _: lose_style, subset=[OddTable.lose])
        style.apply(lambda _: [f'{left}{middle}'] * length, subset=ValueTable.class_columns())
        style.apply(lambda _: handicap_style, subset=HandicapTable.class_columns())
        if file_format == 'special':
            style.apply(lambda _: [f'{calibri}{red}{ten_point}{center}{middle}'] * length, subset=['全场比分'])
            style.data[DataTable.match_number] = '北单' + style.data[DataTable.match_number].astype(str).str.zfill(3)
            style.apply(lambda _: empty_column_style, subset=['空列1', '空列2'])

        exported_time = datetime.now().strftime('%Y%m%d-%H%M%S')

        path = project_path / f'{file_name}.xlsx'
        mkdir(path.parent)

        columns = {column: chr(ord('B') + index) for index, column in enumerate(style.data.columns.values)}

        writer = pd.ExcelWriter(path)

        style.to_excel(writer, sheet_name=exported_time)

        worksheet = writer.sheets[exported_time]

        for cell in worksheet[columns[DataTable.match_time]]:
            cell.number_format = 'yyyy/m/d h:mm'

        for cells in worksheet[f'{columns[OddTable.win]}:{columns[OddTable.lose]}']:
            for cell in cells:
                cell.number_format = '0.00'

        handicap_start = columns[HandicapTable.live_average_water1]
        handicap_end = columns[HandicapTable.early_average_water2]

        for cells in worksheet[f'{handicap_start}:{handicap_end}']:
            for cell in cells:
                cell.number_format = '0.000'

        worksheet.column_dimensions[columns[DataTable.match_time]].width = 12

        worksheet.column_dimensions[columns[DataTable.host_name]].width = 20
        worksheet.column_dimensions[columns[DataTable.guest_name]].width = 20

        worksheet.column_dimensions[columns[DataTable.handicap_name]].width = 10

        worksheet.column_dimensions[columns['结果']].width = 2

        for column in [columns['比分'], columns[DataTable.half_score]]:
            worksheet.column_dimensions[column].width = 4

        if file_format == 'special':
            worksheet.column_dimensions[columns['全场比分']].width = 4

        for i in range(3):
            worksheet.column_dimensions[chr(ord(columns[OddTable.win]) + i)].width = 6

        for i in range(6 if not file_format == 'special' else 8):
            worksheet.column_dimensions[chr(ord(handicap_start) + i)].width = 6

        if file_format == 'special':
            for i in range(2):
                worksheet.column_dimensions[chr(ord(columns['空列1']) + i)].width = 0.001

        save_message(path, lambda: writer.close())
