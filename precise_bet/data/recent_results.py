#  Copyright (C) 2025  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import requests
from bs4 import BeautifulSoup, Tag

from precise_bet.util import post_request_content, request_content


def get_match_recent_results(
    match_id: str, session: requests.Session, ua: str, request_trying_times: int
) -> list[str]:
    url = "https://odds.500.com/fenxi/shuju-" + match_id[1:] + ".shtml"

    text = request_content(
        url, session, ua=ua, encoding="gb2312", trying_times=request_trying_times
    )

    soup = BeautifulSoup(text, "html.parser")

    query_hash = soup.find(id="hash")["value"]

    record = soup.find("div", class_="M_box record")
    tables = record.find_all("div", class_="odds_zj_tubiao")

    result = []

    for table in tables:
        divs = table.find_all("div", recursive=False)
        for div in divs[:2]:
            result += parse_table(
                match_id,
                div,
                query_hash,
                session,
                ua,
                request_trying_times,
            )

    return result


def parse_table(
    match_id: str,
    team_results: Tag,
    query_hash: str,
    session: requests.Session = None,
    ua: str = None,
    request_trying_times: int = None,
) -> list[str]:
    """
    解析球队近期比赛结果

    :param match_id: 比赛 ID
    :param team_results: 带有 `id` 以 `team_zhanji` 开头的 `div` 标签
    :param query_hash: 网页中的查询哈希
    :param session: 请求会话
    :param ua: User-Agent
    :param request_trying_times: 请求尝试次数
    :return: 近 3 场比赛结果
    """

    trs = team_results.find_all("tr")
    trs = trs[2 : len(trs) - 1]

    result = []

    for tr in trs:
        tds = tr.find_all("td")
        if tds[0].text.strip() == "球会友谊" or len(result) >= 3:
            continue
        match_result = tds[5].text.strip()
        if match_result == "胜":
            result.append("win")
        elif match_result == "平":
            result.append("draw")
        elif match_result == "负":
            result.append("lose")

    if session and ua and request_trying_times and len(result) < 3:
        api_variant = team_results["id"][11:].split("_")

        form = team_results.find("div", class_="record_check")
        allowed_match_types = []
        disabled_match_type = ""
        for option in form.find_all("span", class_="mar_right15"):
            match_type = option.find("input")["value"]

            if option.text.strip() == "球会友谊":
                disabled_match_type = match_type
            else:
                allowed_match_types.append(match_type)

        result = get_detailed_recent_results(
            match_id,
            query_hash,
            api_variant[0],
            api_variant[1],
            allowed_match_types,
            disabled_match_type,
            session,
            ua,
            request_trying_times,
        )

    for _ in range(0, 3 - len(result)):
        result.append("unknown")

    return result


def get_detailed_recent_results(
    match_id: str,
    query_hash: str,
    api_variant_parameter_0: str,
    api_variant_parameter_1: str,
    allowed_match_types: list[str],
    disabled_match_type: str,
    session: requests.Session,
    ua: str,
    request_trying_times: int,
) -> list[str]:
    url = (
        "https://odds.500.com/fenxi1/inc/shuju_zhanji"
        + api_variant_parameter_0
        + ".php"
    )

    data = {
        "id": match_id[1:],
        "hash": query_hash,
        "limit": 6,
        "hoa": api_variant_parameter_1,
        "bhbc": 0,
        "callback": "ajax",
        "r": 1,
        f"match[{disabled_match_type}]": -1,
    }

    for match_type in allowed_match_types:
        data[f"match[{match_type}]"] = 1

    text = post_request_content(
        url, data, session, ua=ua, encoding="utf-8", trying_times=request_trying_times
    )

    soup = BeautifulSoup(text, "html.parser")

    return parse_table(match_id, soup, query_hash)
