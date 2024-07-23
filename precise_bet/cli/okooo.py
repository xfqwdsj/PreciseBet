#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from bs4 import BeautifulSoup, Tag
from selenium import webdriver

from precise_bet import rprint
from precise_bet.type import Column, DataTable, MatchTable


def okooo(
    ctx: typer.Context,
    volume_number: Annotated[Optional[int], typer.Argument(help="期号")] = None,
):
    """获取澳客数据"""

    project_path: Path = ctx.obj["project_path"]

    rprint("正在获取数据...")

    browser = webdriver.Edge()

    browser.get(
        f"https://www.okooo.com/livecenter/danchang{f'?date={volume_number}' if volume_number else ''}"
    )

    browser.refresh()
    text = browser.page_source
    browser.close()

    rprint("正在解析数据...")

    data = parse(project_path, text)

    rprint(f"解析成功")

    data.save()


def parse(project_path: Path, html: str) -> DataTable:
    soup = BeautifulSoup(html, "html.parser")

    volume_number = int(soup.find(id="select_qihao").text.strip()[:-1])

    data = OkoooDataTable(project_path).read_or_create()

    data.name_ = f"{data.name_}-{volume_number}"

    trs: list[Tag] = soup.find("tbody").find_all("tr")

    for tr in trs:
        if not tr.has_attr("matchid"):
            continue

        match_id = tr["matchid"]

        if (
            match_id in data.index
            and data.loc[match_id, DataTable.volume_number] > volume_number
        ):
            rprint(
                f"[bold yellow]在第 {volume_number} 期发现重复的比赛 {match_id}，"
                f"已有的数据位于第 {data.loc[match_id, DataTable.volume_number]} 期。"
                "跳过该比赛..."
            )
            continue

        tds: list[Tag] = tr.find_all("td")

        match_number = int(tds[0].text)

        league = tr["type"]

        match_time = datetime.strptime(
            f"{str(volume_number)[:2]}{tds[2].text}", "%y%m-%d %H:%M"
        )

        if volume_number % 100 == 11 and match_time.month == 12:
            match_time = match_time.replace(year=match_time.year - 1)

        match_time = match_time.strftime("%Y/%m/%d %H:%M")

        host = tds[4].find("a").text
        guest = tds[6].find("a").text

        score = tds[5].text.strip().replace("\n", " ")

        data.loc[match_id] = OkoooDataTable.generate_row(
            volume_number=volume_number,
            match_number=match_number,
            league=league,
            match_time=match_time,
            host_name=host,
            score=score,
            guest_name=guest,
        )

    return data


class OkoooDataTable(MatchTable):
    name_ = "okooo-data"

    volume_number = Column("期号", int)
    match_number = Column("场次", int)
    league = Column("赛事", str)
    match_time = Column("比赛时间", str)
    host_name = Column("主队名称", str)
    score = Column("比分", str)
    guest_name = Column("客队名称", str)
