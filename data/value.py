import click
import regex

from util import request_content


def get_team_value(team_id: int, ua: str) -> int:
    url = 'https://liansai.500.com/team/' + str(team_id)

    click.echo('正在获取代号为 {} 的球队价值信息...'.format(team_id))

    text: str
    try:
        text = request_content(url, ua)
    except RuntimeError as err:
        click.echo('{}。将该球队价值设为 -1'.format(err), err=True)
        return -1

    name = regex.search(r'<h2 class="lsnav_qdnav_name">(.+)</h2>', text)
    if name:
        click.echo('球队名称为 {}'.format(name.group(1)))
    else:
        click.echo('未找到球队名称', err=True)

    click.echo('正在匹配...')

    value = regex.search(r'球队身价：&euro; (\d+)万', text)
    if value is None:
        click.echo('匹配失败。将该球队价值设为 -1', err=True)
        return -1

    click.echo('匹配成功，球队价值为 {} 万'.format(value.group(1)))
    return int(value.group(1))
