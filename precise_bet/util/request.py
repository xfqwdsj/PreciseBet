#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import requests
from fake_useragent import UserAgent

from precise_bet import rprint


def request_content(url, ua=UserAgent(platforms=["pc"]).random) -> str:
    rprint(f"正在向 {url} 发送请求（UA：{ua}）...")
    response = requests.get(url, headers={"User-Agent": ua})
    if not response.ok:
        if response.status_code == 503:
            raise RuntimeError(
                f"请求失败，状态码：{response.status_code}，可能是因为访问频率过高导致被暂时封禁"
            )
        raise RuntimeError(f"请求失败，状态码：{response.status_code}")

    response.encoding = "gb2312"
    return response.text
