import click
from bs4 import BeautifulSoup, Tag

from util import request_content


def parse(td: Tag) -> list[float]:
    data_td = td.find_all('td')
    return [float(data_td[0].text), float(data_td[1].text), float(data_td[2].text)]


def get_match_handicap(match_id: str) -> list[float]:
    url = 'https://odds.500.com/fenxi/yazhi-' + match_id[1:] + '.shtml'

    text = request_content(url)

    soup = BeautifulSoup(text, 'html.parser')

    tds = soup.find('tr', attrs={'xls': 'footer'}).find_all('td')

    raw = [tds[3].text, tds[4].text, tds[5].text, tds[9].text, tds[10].text, tds[11].text]
    handicap = [float(i) if i != ' ' else 0 for i in raw]

    click.echo('获取亚盘数据成功，数据为：{}'.format(handicap))

    return handicap
