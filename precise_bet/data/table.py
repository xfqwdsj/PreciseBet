#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from regex import regex

data_columns = ['代号', '场次', '赛事', '轮次', '比赛时间', '状态', '主队', '客队']
score_columns = ['代号', '主队', '客队', '更新时间', '更新时比赛状态']
value_columns = ['代号', '主队价值', '客队价值', '更新时间', '更新时比赛状态']
handicap_columns = ['代号', '平即水1', '平即盘', '平即水2', '平初水1', '平初盘', '平初水2', '更新时间',
                    '更新时比赛状态']
odd_columns = ['代号', '胜', '平', '负', '更新时间', '更新时比赛状态']
league_columns = ['代号', '名称', '颜色']
team_columns = ['代号', '名称', '价值', '更新时间']

match_status = {0: '未开始', 1: '上半场', 2: '中场', 3: '下半场', 4: '已结束', 5: '5', 6: '改期', 7: '腰斩', 8: '中断',
                9: '待定', 10: '10', 11: '11', 12: '点球'}


@dataclass
class DataTable:
    volume_number: int
    data: pd.DataFrame
    score: pd.DataFrame
    value: pd.DataFrame
    handicap: pd.DataFrame
    odd: pd.DataFrame
    league: pd.DataFrame
    team: pd.DataFrame


def parse_table(project_path: Path, html: str) -> DataTable:
    soup = BeautifulSoup(html, features='html.parser')

    volume_number = int(soup.find(id='sel_expect').text.strip())

    data = pd.DataFrame(columns=data_columns).set_index('代号')
    score = pd.DataFrame(columns=score_columns).set_index('代号')
    value: pd.DataFrame
    handicap: pd.DataFrame
    odd = pd.DataFrame(columns=odd_columns).set_index('代号')
    league: pd.DataFrame
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

    league_path = project_path / 'league.csv'
    if league_path.exists():
        league = pd.read_csv(league_path, index_col='代号')
    else:
        league = pd.DataFrame(columns=league_columns).set_index('代号')

    team_path = project_path / 'team.csv'
    if team_path.exists():
        team = pd.read_csv(team_path, index_col='代号')
    else:
        team = pd.DataFrame(columns=team_columns).set_index('代号')

    trs = soup.find('tbody').find_all('tr')

    updated_time = datetime.now().timestamp()

    for tr in trs:
        if tr.has_attr('parentid'):
            continue

        match_id = tr['id']

        tds = tr.find_all('td')

        league_tag = tds[1]
        league_id = urlparse(league_tag.find('a')['href']).path.split('/')[1]

        host_tag = tds[5].find('a')
        guest_tag = tds[7].find('a')
        host_id = int(urlparse(host_tag['href']).path.split('/')[2])
        guest_id = int(urlparse(guest_tag['href']).path.split('/')[2])

        match_time = datetime.strptime(f'{str(volume_number)[:2]}{tds[3].text}', '%y%m-%d %H:%M')
        match_timestamp = int(match_time.astimezone(ZoneInfo('Asia/Shanghai')).timestamp())

        data.loc[match_id] = [int(tds[0].text), league_id, tds[2].text, match_timestamp, int(tr['status']), host_id,
                              guest_id]

        score_tag = tds[6]
        host_score_text = score_tag.find('a', attrs={'class': 'clt1'}).text
        host_score = int(host_score_text if host_score_text != '' else 0)
        guest_score_text = score_tag.find('a', attrs={'class': 'clt3'}).text
        guest_score = int(guest_score_text if guest_score_text != '' else 0)
        score.loc[match_id] = [host_score, guest_score, updated_time, data.loc[match_id, '状态']]

        if match_id not in value.index:
            value.loc[match_id] = [0, 0, -1.0, -1]

        if match_id not in handicap.index:
            handicap.loc[match_id] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1]

        league.loc[league_id] = [league_tag.text, league_tag['bgcolor']]

        if host_id not in team.index:
            team.loc[host_id] = [host_tag.text, 0, -1.0]
        else:
            team.loc[host_id, '名称'] = host_tag.text

        if guest_id not in team.index:
            team.loc[guest_id] = [guest_tag.text, 0, -1.0]
        else:
            team.loc[guest_id, '名称'] = guest_tag.text

    odd_json = regex.search(r'var liveOddsList = ({.*});', html).group(1)
    odd_dict = eval(odd_json)
    for match_id, odds in odd_dict.items():
        match_id = f'a{match_id}'
        odd_list = [0.0, 0.0, 0.0]
        if '0' in odds:
            odd_list = [float(i) for i in odds['0']]
        odd.loc[match_id] = odd_list + [updated_time, data.loc[match_id, '状态']]

    data.sort_values(by='场次', inplace=True)
    league.sort_index(inplace=True)
    team.sort_index(inplace=True)

    return DataTable(volume_number=volume_number, data=data, score=score, value=value, handicap=handicap, odd=odd,
                     league=league, team=team)
