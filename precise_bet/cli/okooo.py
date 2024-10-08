#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from datetime import datetime
from pathlib import Path
from time import sleep
from typing import List
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import typer
from bs4 import BeautifulSoup, Tag
from requests import RequestException

from precise_bet import rprint, rprint_err
from precise_bet.cli.export import (
    bold,
    calibri,
    center,
    middle,
    nine_point,
    odd_background_color,
    red,
    result_color,
    ten_point,
    ya_hei,
)
from precise_bet.type import Column, DataTable, MatchTable
from precise_bet.util import mkdir, request_content


def okooo(
    ctx: typer.Context,
):
    """获取澳客数据"""

    project_path: Path = ctx.obj["project_path"]
    session: requests.Session = ctx.obj["session"]

    start_volume_number: int = typer.prompt("请输入起始期号", type=int)
    end_volume_number: int = typer.prompt("请输入结束期号", type=int)
    interval = typer.prompt("请输入请求间隔", type=int)

    rprint("正在获取数据...")

    rprint("第一次请求是为了模拟正常访问，可能会出现 405 错误")

    try:
        request_content("https://www.okooo.com/livecenter/danchang", session)
    except RequestException as e:
        if e.response.status_code != 405:
            rprint_err(e)
            return

        rprint("捕捉到 405 错误，继续请求...")

    volume_number = start_volume_number

    while volume_number <= end_volume_number:
        if volume_number != start_volume_number:
            rprint(f"等待 {interval} 秒...")
            sleep(interval)

        text: str
        try:
            text = request_content(
                f"https://www.okooo.com/livecenter/danchang{f'?date={volume_number}' if volume_number else ''}",
                session,
                encoding="gb2312",
            )
        except RequestException as e:
            rprint_err(e)
            return

        rprint("正在解析数据...")

        data = parse(project_path, text)

        rprint(f"解析成功")

        data.save()

        save_path = project_path / "okooo" / f"{volume_number}.xlsx"
        mkdir(save_path.parent)

        data[OkoooDataTable.match_number] = (
            data[OkoooDataTable.match_number].astype(str).str.zfill(3)
        )

        timezone = datetime.now().astimezone().tzinfo
        data[OkoooDataTable.match_time] = (
            pd.to_datetime(data[OkoooDataTable.match_time], unit="s", utc=True)
            .dt.tz_convert(timezone)
            .dt.tz_localize(None)
        )

        odd_style = f"{calibri}{ten_point}{center}{middle}"
        sp_win_style = [
            (odd_background_color if r == "胜" else "") + odd_style
            for r in data[OkoooDataTable.result]
        ]
        sp_draw_style = [
            (odd_background_color if r == "平" else "") + odd_style
            for r in data[OkoooDataTable.result]
        ]
        sp_lose_style = [
            (odd_background_color if r == "负" else "") + odd_style
            for r in data[OkoooDataTable.result]
        ]

        length = len(data)
        style = data.style
        style.apply(
            lambda _: [f"{red}{bold}"] * length,
            subset=[OkoooDataTable.match_number, OkoooDataTable.score],
        )
        style.apply(lambda _: sp_win_style, subset=[OkoooDataTable.sp_win])
        style.apply(lambda _: sp_draw_style, subset=[OkoooDataTable.sp_draw])
        style.apply(lambda _: sp_lose_style, subset=[OkoooDataTable.sp_lose])
        style.apply(
            lambda _: [f"{ya_hei}{result_color}{nine_point}{center}{middle}"] * length,
            subset=[OkoooDataTable.result],
        )

        writer = pd.ExcelWriter(save_path)
        style.to_excel(writer)

        worksheet = writer.sheets["Sheet1"]

        for cell in worksheet["E"]:
            cell.number_format = "yyyy/m/d h:mm"

        for cells in worksheet["I:K"]:
            for cell in cells:
                cell.number_format = "0.00"

        worksheet.column_dimensions["A"].width = 8
        worksheet.column_dimensions["B"].width = 6
        worksheet.column_dimensions["C"].width = 5
        worksheet.column_dimensions["D"].width = 10
        worksheet.column_dimensions["E"].width = 18
        worksheet.column_dimensions["F"].width = 20
        worksheet.column_dimensions["G"].width = 6
        worksheet.column_dimensions["H"].width = 20
        worksheet.column_dimensions["I"].width = 5
        worksheet.column_dimensions["J"].width = 5
        worksheet.column_dimensions["K"].width = 5
        worksheet.column_dimensions["L"].width = 5

        writer.close()

        if volume_number % 10 == 5:
            volume_number += 6
        else:
            volume_number += 1
        if int(volume_number % 1000 / 10) == 13:
            volume_number += 880


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

        host = tds[4].find("a").text + tds[4].find_all("span")[2].text
        guest = tds[6].find("a").text

        score = tds[5].text.strip().replace("\n", " ")

        sp_tags: List[Tag] = tds[9].find_all("span")

        result_text = tds[10].text.strip()
        if result_text == "0":
            result = "负"
        elif result_text == "1":
            result = "平"
        elif result_text == "3":
            result = "胜"
        else:
            result = ""

        data.loc[match_id] = OkoooDataTable.generate_row(
            volume_number=volume_number,
            match_number=match_number,
            league=league,
            match_time=int(
                match_time.astimezone(ZoneInfo("Asia/Shanghai")).timestamp()
            ),
            host_name=host,
            score=score,
            guest_name=guest,
            sp_win=float(sp_tags[0].text),
            sp_draw=float(sp_tags[1].text),
            sp_lose=float(sp_tags[2].text),
            result=result,
        )

    return data


class OkoooDataTable(MatchTable):
    name_ = "okooo-data"

    volume_number = Column("期号", int)
    match_number = Column("场次", int)
    league = Column("赛事", str)
    match_time = Column("比赛时间", int)
    host_name = Column("主队名称", str)
    score = Column("比分", str)
    guest_name = Column("客队名称", str)
    sp_win = Column("胜", float)
    sp_draw = Column("平", float)
    sp_lose = Column("负", float)
    result = Column("结果", str)
