import click
import requests
from fake_useragent import UserAgent


def request_content(url, ua=UserAgent().random) -> str:
    click.echo('正在向 {} 发送请求（UA：{}）...'.format(url, ua))
    response = requests.get(url, headers={'User-Agent': ua})
    if not response.ok:
        raise RuntimeError('请求失败，状态码：{}'.format(response.status_code))

    response.encoding = 'gb2312'
    return response.text
