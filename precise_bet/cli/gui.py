#  Copyright (C) 2025  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import tkinter as tk
from pathlib import Path
from typing import Callable

import typer

from precise_bet.cli.flow import flow


def gui(ctx: typer.Context):
    root = tk.Tk(className="简单的界面")

    entries: dict[str, (tk.Widget, Callable[[tk.Widget], any])] = {}

    row = 0

    tk.Label(root, text="项目路径（不用填）").grid(row=row)
    entries["project_path"] = (tk.Entry(root), lambda entry: entry.get())
    entries["project_path"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="*期号").grid(row=row)
    entries["volume_number"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["volume_number"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="更新范围（时，默认 6）").grid(row=row)
    entries["break_hours"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["break_hours"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="更新球队价值（总开关）").grid(row=row)
    update_value = tk.BooleanVar(value=True)
    entries["update_value"] = (
        tk.Checkbutton(root, variable=update_value),
        lambda _: update_value.get(),
    )
    entries["update_value"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="只获取未获取过的比赛的球队价值").grid(row=row)
    only_new_value = tk.BooleanVar(value=True)
    entries["only_new_value"] = (
        tk.Checkbutton(root, variable=only_new_value),
        lambda _: only_new_value.get(),
    )
    entries["only_new_value"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="更新盘口（总开关）").grid(row=row)
    update_handicap = tk.BooleanVar(value=True)
    entries["update_handicap"] = (
        tk.Checkbutton(root, variable=update_handicap),
        lambda _: update_handicap.get(),
    )
    entries["update_handicap"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="更新最近比赛结果（总开关）").grid(row=row)
    update_recent_results = tk.BooleanVar(value=True)
    entries["update_recent_results"] = (
        tk.Checkbutton(root, variable=update_recent_results),
        lambda _: update_recent_results.get(),
    )
    entries["update_recent_results"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="循环执行次数（默认 1，0 为无限循环）").grid(row=row)
    entries["execute_times"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["execute_times"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="循环执行间隔（秒，默认 0）").grid(row=row)
    entries["flow_interval"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["flow_interval"][0].grid(row=row, column=1)
    row += 1

    tk.Label(
        root,
        text="在指定时间后终止程序（秒，默认不终止，仅在流程中的一个步骤结束之后才会终止）",
    ).grid(row=row)
    entries["terminate_time"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["terminate_time"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="所有网络请求尝试次数（默认 1，设为 0 无限尝试）").grid(row=row)
    entries["request_trying_times"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["request_trying_times"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="整个流程遇到意外错误的时候的重试次数（默认 3）").grid(row=row)
    entries["retry_times"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["retry_times"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="普通更新间隔时间（秒，默认 5）").grid(row=row)
    entries["interval"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["interval"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="额外更新间隔时间（秒，默认 60）").grid(row=row)
    entries["extra_interval"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["extra_interval"][0].grid(row=row, column=1)
    row += 1

    tk.Label(
        root, text="额外间隔概率（随机以额外更新间隔时间暂停程序的概率，默认 0）"
    ).grid(row=row)
    entries["extra_interval_probability"] = (
        tk.Entry(root),
        lambda entry: float(entry.get()),
    )
    entries["extra_interval_probability"][0].grid(row=row, column=1)
    row += 1

    tk.Label(
        root, text="间隔时间偏移量范围（默认 2 则在 ±2 范围内随机调整间隔时间）"
    ).grid(row=row)
    entries["interval_offset_range"] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries["interval_offset_range"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="快速模式（将间隔时间和额外间隔概率设为 0）").grid(row=row)
    fast_mode = tk.BooleanVar(value=False)
    entries["fast_mode"] = (
        tk.Checkbutton(root, variable=fast_mode),
        lambda _: fast_mode.get(),
    )
    entries["fast_mode"][0].grid(row=row, column=1)
    row += 1

    tk.Label(root, text="只导出当前期").grid(row=row)
    export_only_current_volume = tk.BooleanVar(value=True)
    entries["export_only_current_volume"] = (
        tk.Checkbutton(root, variable=export_only_current_volume),
        lambda _: export_only_current_volume.get(),
    )
    entries["export_only_current_volume"][0].grid(row=row, column=1)
    row += 1

    tk.Label(
        root, text="导出场次范围（默认全部，需要开启“只导出当前期”，格式如 1-3）"
    ).grid(row=row)
    entries["export_match_number_range"] = (tk.Entry(root), lambda entry: entry.get())
    entries["export_match_number_range"][0].grid(row=row, column=1)
    row += 1

    def run_flow():
        project_path = entries["project_path"][0].get()
        if project_path:
            ctx.obj["project_path"] = Path(project_path)

        arguments = {}

        for key, entry in entries.items():
            if key == "project_path":
                continue

            value: any

            try:
                value = entry[1](entry[0])
            except Exception:
                continue

            arguments[key] = value

        flow(ctx, **arguments)

    tk.Button(root, text="运行", command=run_flow).grid(row=row, column=1)

    root.mainloop()
