#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import regex

from precise_bet import rprint
from precise_bet.util import request_content


def get_team_value(team_id: int, ua: str) -> int:
    url = 'https://liansai.500.com/team/' + str(team_id)

    rprint(f'正在获取代号为 [bold]{team_id}[/bold] 的球队价值信息...')

    text = request_content(url, ua)

    name = regex.search(r'<h2 class="lsnav_qdnav_name">(.+)</h2>', text)
    if name:
        rprint(f'球队名称为 [bold blue]{name.group(1)}[/bold blue]')
    else:
        rprint('[bold yellow]未找到球队名称')

    rprint('正在匹配...')

    value = regex.search(r'球队身价：&euro; (\d+)万', text)
    if value is None:
        rprint('[bold yellow]匹配失败。将该球队价值设为 0')
        return 0

    return int(value.group(1))
