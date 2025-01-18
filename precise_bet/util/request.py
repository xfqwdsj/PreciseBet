#  Copyright (C) 2025  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from typing import Callable

import requests
from fake_useragent import UserAgent
from requests import RequestException

from precise_bet import rprint


def request_base(
    func: Callable[[], requests.Response],
    encoding: str = None,
    trying_times=1,
) -> str:
    tried = False
    while True:
        if tried:
            rprint(
                f"正在重试请求，剩余尝试次数：{trying_times if trying_times > 0 else '无限'}"
            )
        tried = True
        try:
            response = func()
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


def request_content(
    url,
    session: requests.Session,
    ua=UserAgent(platforms=["desktop"]).random,
    encoding: str = None,
    trying_times=1,
) -> str:
    rprint(f"正在向 {url} 发送请求（UA：{ua}）...")
    return request_base(
        lambda: session.get(url, headers={"User-Agent": ua}),
        encoding=encoding,
        trying_times=trying_times,
    )


def post_request_content(
    url,
    data: dict,
    session: requests.Session,
    ua=UserAgent(platforms=["desktop"]).random,
    encoding: str = None,
    trying_times=1,
) -> str:
    rprint(f"正在向 {url} 发送请求（UA：{ua}）...")
    return request_base(
        lambda: session.post(url, data, headers={"User-Agent": ua}),
        encoding=encoding,
        trying_times=trying_times,
    )
