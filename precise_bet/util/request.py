#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import requests
from fake_useragent import UserAgent
from requests import RequestException

from precise_bet import rprint


def request_content(
    url,
    session: requests.Session,
    ua=UserAgent(platforms=["pc"]).random,
    encoding: str = None,
    trying_times=1,
) -> str:
    rprint(f"正在向 {url} 发送请求（UA：{ua}）...")
    tried = False
    while True:
        if tried:
            rprint(
                f"正在重试请求，剩余尝试次数：{trying_times if trying_times > 0 else '无限'}"
            )
        tried = True
        try:
            response = session.get(url, headers={"User-Agent": ua})
            if response.ok:
                if encoding:
                    response.encoding = encoding
                return response.text
            else:
                if response.status_code == 503:
                    error_message = f"请求失败，可能是因为访问频率过高导致被暂时封禁"
                else:
                    error_message = f"请求失败，状态码：{response.status_code}"
                raise RequestException(error_message, response=response)
        except RequestException as e:
            rprint(f"请求过程中发生错误：{e}")
            if trying_times == 0:
                continue
            trying_times -= 1
            if trying_times < 1:
                raise e
