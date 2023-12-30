#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import tkinter as tk
from typing import Callable

import typer

from precise_bet.cli.flow import flow


def gui(ctx: typer.Context):
    root = tk.Tk(className='简单的界面')

    entries: dict[str, (tk.Widget, Callable[[tk.Widget], any])] = {}

    tk.Label(root, text='项目路径（不用填）').grid(row=0)
    entries['project_path'] = (tk.Entry(root), lambda entry: entry.get())
    entries['project_path'][0].grid(row=0, column=1)

    tk.Label(root, text='*期号').grid(row=1)
    entries['volume_number'] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries['volume_number'][0].grid(row=1, column=1)

    tk.Label(root, text='更新球队价值').grid(row=2)
    full_update = tk.BooleanVar(value=True)
    entries['full_update'] = (tk.Checkbutton(root, variable=full_update), lambda _: full_update.get())
    entries['full_update'][0].grid(row=2, column=1)

    tk.Label(root, text='循环执行次数（默认 1，0 为无限循环）').grid(row=3)
    entries['execute_times'] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries['execute_times'][0].grid(row=3, column=1)

    tk.Label(root, text='循环执行间隔（秒，默认 0）').grid(row=4)
    entries['flow_interval'] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries['flow_interval'][0].grid(row=4, column=1)

    tk.Label(root, text='遇到错误的时候的重试次数（默认 3）').grid(row=5)
    entries['retry_times'] = (tk.Entry(root), lambda entry: int(entry.get()))
    entries['retry_times'][0].grid(row=5, column=1)

    tk.Label(root, text='额外间隔概率（默认 0）').grid(row=6)
    entries['extra_interval_probability'] = (tk.Entry(root), lambda entry: float(entry.get()))
    entries['extra_interval_probability'][0].grid(row=6, column=1)

    tk.Label(root, text='快速模式').grid(row=7)
    fast_mode = tk.BooleanVar(value=False)
    entries['fast_mode'] = (tk.Checkbutton(root, variable=fast_mode), lambda _: fast_mode.get())
    entries['fast_mode'][0].grid(row=7, column=1)

    def run_flow():
        project_path = entries['project_path'][0].get()
        if project_path:
            ctx.obj['project_path'] = project_path

        arguments = {}

        for key, entry in entries.items():
            if key == 'project_path':
                continue

            value: any

            try:
                value = entry[1](entry[0])
            except Exception:
                continue

            arguments[key] = value

        flow(ctx, **arguments)

    tk.Button(root, text='运行', command=run_flow).grid(row=8, column=1)

    root.mainloop()
