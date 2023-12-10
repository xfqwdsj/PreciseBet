#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from datetime import datetime
from pathlib import Path

import click
import pandas as pd
from click_option_group import optgroup

from precise_bet.data import DataTable, HandicapTable, LeagueTable, MatchTable, OddTable, ScoreTable, ValueTable, \
    match_status, save_message, save_to_csv

red = 'color: #FF0000;'
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
@optgroup.option('--file-name', '-n', help='导出文件名', default='data', type=str)
@optgroup.option('--file-format', '-f', help='导出文件格式', prompt='请输入文件格式', default='csv',
                 type=click.Choice(['csv', 'excel', 'special']))
def export(ctx, file_name: str, file_format: str):
    """
    导出数据
    """

    project_path: Path = ctx.obj['project_path']

    click.echo('开始导出数据...')

    data = pd.DataFrame(columns=[MatchTable.match_id]).set_index(MatchTable.match_id)

    league = LeagueTable(project_path).read()

    for volume in project_path.iterdir():
        if not volume.is_dir():
            continue

        volume_number = int(volume.name)

        click.echo(f'正在处理第 {volume_number} 期数据...')

        volume_data = DataTable(project_path, volume_number).read()
        score = ScoreTable(project_path, volume_number).read()
        value = ValueTable(project_path, volume_number).read()
        handicap = HandicapTable(project_path, volume_number).read()
        odd = OddTable(project_path, volume_number).read()

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

        volume_data.insert(0, '期号', volume_number)
        # '+' 为特殊运算符，表示合并，不可替换为模板字符串
        volume_data.insert(8, '比分',
                           score[ScoreTable.host_score].astype(str) + ' - ' + score[ScoreTable.guest_score].astype(str))
        volume_data[OddTable.class_columns()] = odd[OddTable.class_columns()]
        volume_data['结果'] = volume_data['比分'].apply(calculate_result)
        volume_data.loc[
            volume_data[DataTable.match_status] != 4, ['比分', '结果']] = '-' if file_format == 'csv' else ''
        volume_data[ValueTable.class_columns()] = value[ValueTable.class_columns()]
        volume_data[HandicapTable.class_columns()[:3]] = handicap[HandicapTable.class_columns()[:3]]
        if file_format == 'special':
            volume_data['空列1'] = ''
            volume_data['空列2'] = ''
        volume_data[HandicapTable.class_columns()[3:]] = handicap[HandicapTable.class_columns()[3:]]

        data = pd.concat([data, volume_data])

    timezone = datetime.now().astimezone().tzinfo

    data[DataTable.match_time] = pd.to_datetime(data[DataTable.match_time], unit='s', utc=True).dt.tz_convert(timezone)
    data.drop(columns=[DataTable.host_id, DataTable.guest_id], inplace=True)

    half_score = data[DataTable.half_score]
    if is_excel(file_format):
        half_score = half_score.apply(lambda x: '' if x == '-' else x)
    if file_format == 'special':
        data.drop(columns=[DataTable.half_score], inplace=True)
    data[DataTable.half_score] = half_score

    status = data[DataTable.match_status].map(match_status)
    if file_format == 'special':
        data.drop(columns=[DataTable.match_status], inplace=True)
    data[DataTable.match_status] = status

    if file_format == 'csv':
        data[DataTable.league_id] = data[DataTable.league_id].map(league[LeagueTable.name])
        save_to_csv(data, project_path, file_name)
    elif is_excel(file_format):
        data[DataTable.match_time] = data[DataTable.match_time].dt.tz_localize(None)
        league_styles = data[DataTable.league_id].map(league[LeagueTable.color])
        league_styles = league_styles.apply(lambda x: f'color: white;background-color: {x};'
                                                      f'{ya_hei}{nine_point}{center}{middle}')
        data[DataTable.league_id] = data[DataTable.league_id].map(league[LeagueTable.name])

        handicap_style = []
        if file_format == 'special':
            empty_column_style = []
        for match_id in data.index:
            color = ''
            if data.loc[match_id, HandicapTable.early_average_handicap] > 0:
                color = handicap_highlight_color
            elif data.loc[match_id, HandicapTable.early_average_handicap] == 0:
                if data.loc[match_id, HandicapTable.live_average_handicap] > 0:
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
        style.apply(lambda _: [f'{ya_hei}{nine_point}{center}{middle}'] * length,
                    subset=['期号', DataTable.match_number])
        style.apply(lambda _: league_styles, subset=[DataTable.league_id])
        style.apply(lambda _: [f'{nine_point}{left}{middle}'] * length, subset=[DataTable.round_number])
        style.apply(lambda _: [f'{calibri}{nine_point}{left}{middle}'] * length, subset=[DataTable.match_time])
        style.apply(lambda _: [f'{ten_point}{middle}'] * length, subset=[DataTable.host_name, DataTable.guest_name])
        style.apply(lambda _: [f'{calibri}{red}{ten_point}{center}{middle}'] * length, subset=['比分'])
        style.apply(lambda _: [f'{calibri}{half_score_color}{ten_point}{center}{middle}'] * length,
                    subset=[DataTable.half_score])
        style.apply(lambda _: [f'{ya_hei}{result_color}{nine_point}{center}{middle}'] * length, subset=['结果'])
        style.apply(lambda _: win_style, subset=[OddTable.win])
        style.apply(lambda _: draw_style, subset=[OddTable.draw])
        style.apply(lambda _: lose_style, subset=[OddTable.lose])
        style.apply(lambda _: [f'{left}{middle}'] * length, subset=ValueTable.class_columns())
        style.apply(lambda _: handicap_style, subset=HandicapTable.class_columns())
        if file_format == 'special':
            def add_zeros(number: int):
                if number < 10:
                    return '00' + str(number)
                elif number < 100:
                    return '0' + str(number)
                else:
                    return str(number)

            style.data[DataTable.match_number] = '北单' + style.data[DataTable.match_number].apply(add_zeros)
            style.apply(lambda _: empty_column_style, subset=['空列1', '空列2'])

        exported_time = datetime.now().strftime('%Y%m%d-%H%M%S')

        path = project_path / f'{file_name}.xlsx'

        columns = {column: chr(ord('B') + index) for index, column in enumerate(style.data.columns.values)}

        writer = pd.ExcelWriter(path)

        style.to_excel(writer, sheet_name=exported_time)

        worksheet = writer.sheets[exported_time]

        for cell in worksheet[columns[DataTable.match_time]]:
            cell.number_format = 'yyyy/m/d h:mm'

        worksheet.column_dimensions[columns[DataTable.match_time]].width = 15

        handicap_start = columns[HandicapTable.live_average_water1]
        handicap_end = columns[HandicapTable.early_average_water2]

        for cells in worksheet[f'{handicap_start}:{handicap_end}']:
            for cell in cells:
                cell.number_format = '0.000'

        worksheet.column_dimensions[columns[DataTable.host_name]].width = 20
        worksheet.column_dimensions[columns[DataTable.guest_name]].width = 20

        for i in range(3):
            worksheet.column_dimensions[chr(ord(columns[OddTable.win]) + i)].width = 6

        for i in range(6 if not file_format == 'special' else 8):
            worksheet.column_dimensions[chr(ord(handicap_start) + i)].width = 6

        if file_format == 'special':
            for i in range(2):
                worksheet.column_dimensions[chr(ord(columns['空列1']) + i)].width = 0.001

        save_message(path, lambda: writer.close())
