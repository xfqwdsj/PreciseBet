#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup

data_columns = ['代号', '场次', '赛事', '轮次', '比赛时间', '状态', '主队', '客队']
value_columns = ['代号', '主队价值', '客队价值', '更新时间', '已固定']
handicap_columns = ['代号', '平即水1', '平即盘', '平即水2', '平初水1', '平初盘', '平初水2', '更新时间', '已固定']
league_columns = ['代号', '颜色']
team_columns = ['代号', '名称', '价值', '更新时间']

match_status = {0: '未开始', 1: '上半场', 2: '中场', 3: '下半场', 4: '已结束', 5: '5', 6: '改期', 7: '7', 8: '中断',
                9: '待定', 10: '10', 11: '11', 12: '点球'}


@dataclass
class DataTable:
    volume_number: int
    data: pd.DataFrame
    value: pd.DataFrame
    handicap: pd.DataFrame
    league: pd.DataFrame
    team: pd.DataFrame


def parse_table(project_path: Path, html: str) -> DataTable:
    soup = BeautifulSoup(html, features='html.parser')

    volume_number = int(soup.find(id='sel_expect').text.strip())

    data = pd.DataFrame(columns=data_columns).set_index('代号')
    value: pd.DataFrame
    handicap: pd.DataFrame
    league = pd.DataFrame(columns=league_columns).set_index('代号')
    team: pd.DataFrame

    value_path = project_path / str(volume_number) / 'value.csv'
    if value_path.exists():
        value = pd.read_csv(value_path, index_col='代号')
    else:
        value = pd.DataFrame(columns=value_columns).set_index('代号')

    handicap_path = project_path / str(volume_number) / 'handicap.csv'
    if handicap_path.exists():
        handicap = pd.read_csv(handicap_path, index_col='代号')
    else:
        handicap = pd.DataFrame(columns=handicap_columns).set_index('代号')

    team_path = project_path / 'team.csv'
    if team_path.exists():
        team = pd.read_csv(team_path, index_col='代号')
    else:
        team = pd.DataFrame(columns=team_columns).set_index('代号')

    trs = soup.find('tbody').find_all('tr')

    for tr in trs:
        if tr.has_attr('parentid'):
            continue

        match_id = tr['id']

        tds = tr.find_all('td')

        host = tds[5].find('a')
        guest = tds[7].find('a')
        host_id = int(urlparse(host['href']).path.split('/')[2])
        guest_id = int(urlparse(guest['href']).path.split('/')[2])
        match_time = datetime.strptime(str(volume_number)[:2] + tds[3].text, '%y%m-%d %H:%M')
        match_timestamp = match_time.astimezone(ZoneInfo('Asia/Shanghai')).timestamp()

        data.loc[match_id] = [int(tds[0].text), tds[1].text, tds[2].text, match_timestamp, int(tr['status']), host_id,
                              guest_id]

        if match_id not in value.index:
            value.loc[match_id] = [0, 0, -1.0, False]

        if match_id not in handicap.index:
            handicap.loc[match_id] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, False]

        league_code = urlparse(tds[1].find('a')['href']).path.split('/')[1]

        league.loc[league_code] = tds[1]['bgcolor']

        if host_id not in team.index:
            team.loc[host_id] = [host.text, 0, -1.0]
        else:
            team.loc[host_id, '名称'] = host.text

        if guest_id not in team.index:
            team.loc[guest_id] = [guest.text, 0, -1.0]
        else:
            team.loc[guest_id, '名称'] = guest.text

    data.sort_values(by='场次', inplace=True)
    league.sort_index(inplace=True)
    team.sort_index(inplace=True)

    return DataTable(volume_number, data, value, handicap, league, team)
