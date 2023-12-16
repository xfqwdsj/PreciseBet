#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Tag
# noinspection PyProtectedMember
from regex import regex

from precise_bet import rprint
from precise_bet.type import DataTable, HandicapTable, LeagueTable, OddTable, ScoreTable, TeamTable, ValueTable


@dataclass
class DataSet:
    volume_number: int
    data: DataTable
    score: ScoreTable
    value: ValueTable
    handicap: HandicapTable
    odd: OddTable
    league: LeagueTable
    team: TeamTable


def parse_table(project_path: Path, html: str) -> DataSet:
    soup = BeautifulSoup(html, features='html.parser')

    volume_number = int(soup.find(id='sel_expect').text.strip())

    data = DataTable(project_path).read_or_create()
    score = ScoreTable(project_path).read_or_create()
    value = ValueTable(project_path).read_or_create()
    handicap = HandicapTable(project_path).read_or_create()
    odd = OddTable(project_path).read_or_create()
    league = LeagueTable(project_path).read_or_create()
    team = TeamTable(project_path).read_or_create()

    trs: list[Tag] = soup.find('tbody').find_all('tr')

    updated_time = datetime.now().timestamp()

    for tr in trs:
        if tr.has_attr('parentid'):
            continue

        match_id = tr['id']

        if match_id in data.index and data.loc[match_id, DataTable.volume_number] > volume_number:
            rprint(
                f'[bold yellow]在第 {volume_number} 期发现重复的比赛 {match_id}，'
                f'已有的数据位于第 {data.loc[match_id, DataTable.volume_number]} 期。'
                '跳过该比赛...'
            )
            continue

        tds: list[Tag] = tr.find_all('td')

        league_tag = tds[1]
        league_id = urlparse(league_tag.find('a')['href']).path.split('/')[1]

        match_status = int(tr['status'])

        host_full_tag = tds[5]
        guest_full_tag = tds[7]
        host_tag = host_full_tag.find('a')
        guest_tag = guest_full_tag.find('a')
        host_id = int(urlparse(host_tag['href']).path.split('/')[2])
        guest_id = int(urlparse(guest_tag['href']).path.split('/')[2])

        match_time = datetime.strptime(f'{str(volume_number)[:2]}{tds[3].text}', '%y%m-%d %H:%M')
        match_timestamp = int(match_time.astimezone(ZoneInfo('Asia/Shanghai')).timestamp())

        score_tag = tds[6]
        host_score_text = score_tag.find('a', attrs={'class': 'clt1'}).text
        host_score = int(host_score_text if host_score_text != '' else 0)
        guest_score_text = score_tag.find('a', attrs={'class': 'clt3'}).text
        guest_score = int(guest_score_text if guest_score_text != '' else 0)
        handicap_name = score_tag.find_all('a')[1].text

        score.loc[match_id] = ScoreTable.generate_row(
            host_score=host_score, guest_score=guest_score, updated_time=updated_time, updated_match_status=match_status
        )

        data.loc[match_id] = DataTable.generate_row(
            volume_number=volume_number, match_number=int(tds[0].text), league_id=league_id, round_number=tds[2].text,
            match_time=match_timestamp, match_status=match_status, host_id=host_id, host_name=host_full_tag.text,
            guest_id=guest_id, guest_name=guest_full_tag.text, half_score=tds[8].text.strip(),
            handicap_name=handicap_name
        )

        if match_id not in value.index:
            value.loc[match_id] = ValueTable.empty_row()

        if match_id not in handicap.index:
            handicap.loc[match_id] = HandicapTable.empty_row()

        if league_id not in league.index:
            league.loc[league_id] = LeagueTable.empty_row(name=league_tag.text, color=league_tag['bgcolor'])
        else:
            league.update_name_and_color(league_id, league_tag.text, league_tag['bgcolor'])

        if host_id not in team.index:
            team.loc[host_id] = TeamTable.empty_row(host_tag.text)
        else:
            team.loc[host_id, TeamTable.name] = host_tag.text

        if guest_id not in team.index:
            team.loc[guest_id] = TeamTable.empty_row(guest_tag.text)
        else:
            team.loc[guest_id, TeamTable.name] = guest_tag.text

    odd_json = regex.search(r'var liveOddsList = ({.*});', html).group(1)
    odd_dict = eval(odd_json)
    for match_id, odds in odd_dict.items():
        match_id = f'a{match_id}'
        odd_list = [0.0, 0.0, 0.0]
        if '0' in odds:
            odd_list = [float(i) for i in odds['0']]
        odd.loc[match_id] = OddTable.row_from_list(odd_list, updated_time, data.loc[match_id, DataTable.match_status])

    data.sort_values(by=[DataTable.volume_number, DataTable.match_number], inplace=True)
    league.sort_index(inplace=True)
    team.sort_index(inplace=True)

    return DataSet(
        volume_number=volume_number, data=data, score=score, value=value, handicap=handicap, odd=odd, league=league,
        team=team
    )
