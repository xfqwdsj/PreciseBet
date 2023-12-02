import click
from bs4 import BeautifulSoup, Tag

from util import request_content


def parse(td: Tag) -> list[float]:
    data_td = td.find_all('td')
    return [float(data_td[0].text), float(data_td[1].text), float(data_td[2].text)]


def get_match_handicap(match_id: str) -> list[float]:
    url = 'https://odds.500.com/fenxi/yazhi-' + match_id[1:] + '.shtml'

    text: str
    try:
        text = request_content(url)
    except RuntimeError as err:
        click.echo('{}。将该场比赛亚盘数据全部设为 0'.format(err), err=True)
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    soup = BeautifulSoup(text, 'html.parser')

    tds = soup.find('tr', attrs={'xls': 'footer'}).find_all('td')

    handicap = [float(tds[3].text), float(tds[4].text), float(tds[5].text), float(tds[9].text), float(tds[10].text), float(tds[11].text)]

    click.echo('获取亚盘数据成功，数据为：{}'.format(handicap))

    return handicap
