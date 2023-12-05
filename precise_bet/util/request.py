#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import click
import requests
from fake_useragent import UserAgent


def request_content(url, ua=UserAgent().random) -> str:
    click.echo('正在向 {} 发送请求（UA：{}）...'.format(url, ua))
    response = requests.get(url, headers={'User-Agent': ua})
    if not response.ok:
        if response.status_code == 503:
            raise RuntimeError('请求失败，状态码：{}，可能是因为访问频率过高导致被暂时封禁'.format(response.status_code))
        raise RuntimeError('请求失败，状态码：{}'.format(response.status_code))

    response.encoding = 'gb2312'
    return response.text
