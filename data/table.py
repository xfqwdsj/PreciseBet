from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup

data_columns = ['代号', '场次', '赛事', '轮次', '比赛时间', '状态', '主队', '客队']
value_columns = ['代号', '主队价值', '客队价值', '更新时间', '已固定']
handicap_columns = ['代号', '平即盘1', '平即水', '平即盘2', '平初盘1', '平初水', '平初盘2', '更新时间', '已固定']
league_columns = ['代号', '颜色']
team_columns = ['代号', '名称', '价值', '更新时间']

match_status = {
    0: '未开始',
    1: '上半场',
    2: '中场',
    3: '下半场',
    4: '已结束',
    6: '改期',
}


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
        utc_8_match_time = datetime.strptime(str(volume_number)[:2] + tds[3].text, '%y%m-%d %H:%M')
        utc_match_time = int((utc_8_match_time - timedelta(hours=8)).timestamp())

        data.loc[match_id] = [int(tds[0].text), tds[1].text, tds[2].text, utc_match_time, int(tr['status']), host_id,
                              guest_id]

        if match_id not in value.index:
            value.loc[match_id] = [-1, -1, -1.0, False]

        if match_id not in handicap.index:
            handicap.loc[match_id] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, False]

        league_code = urlparse(tds[1].find('a')['href']).path.split('/')[1]

        if league_code not in league.index:
            league.loc[league_code] = tds[1]['bgcolor']

        if host_id not in team.index:
            team.loc[host_id] = [host.text, -1, -1.0]

        if guest_id not in team.index:
            team.loc[guest_id] = [guest.text, -1, -1.0]

    data.sort_values(by='场次', inplace=True)
    league.sort_index(inplace=True)
    team.sort_index(inplace=True)

    return DataTable(volume_number, data, value, handicap, league, team)
