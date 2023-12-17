#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import typer

from precise_bet import rprint, rule
from precise_bet.cli.export import ExportFileFormats, export
from precise_bet.cli.generate_data import generate_data
from precise_bet.cli.update import Actions as UpdateActions, update
from precise_bet.util import sleep


def flow(
        ctx: typer.Context, volume_number: int, full_update: bool = True, flow_interval: int = 0, retry_times: int = 3,
        extra_interval_probability: float = 0, execute_times: int = 1
):
    """生成数据、更新数据、导出数据"""

    if retry_times < 0:
        retry_times = 0

    executed_times = 0

    step = 0
    error_times = 0

    while execute_times < 1 or executed_times < execute_times:
        try:
            retry_indicator = '[bold]从中断处继续[/bold]' if step > 0 else ''
            total_indicator = f' / [blue]{execute_times}[/blue]' if execute_times >= 1 else ''
            rule(
                f'正在{retry_indicator}执行第 [yellow]{executed_times + 1}[/yellow]{total_indicator} 次流程'
                '（按下 [bold]Ctrl[/bold] + [bold]C[/bold] 中断）'
            )

            if step == 0:
                generate_data(ctx, volume_number=volume_number)
                step += 1

            if step == 1:
                if full_update:
                    update(
                        ctx, action=UpdateActions.value_action.value, volume_number=volume_number,
                        extra_interval_probability=extra_interval_probability, only_new=True
                    )
                step += 1

            if step == 2:
                update(
                    ctx, action=UpdateActions.handicap_action.value, volume_number=volume_number,
                    extra_interval_probability=extra_interval_probability
                )
        except KeyboardInterrupt:
            rule('[bold red]正在中断，再次按下 [bold]Ctrl[/bold] + [bold]C[/bold] 强制中断')
            break
        except Exception as e:
            error_times += 1
            if error_times > retry_times:
                raise e
            rprint(e)
            rule(f'[bold red]发生错误，正在重试（第 {error_times} / {retry_times} 次）')
        else:
            executed_times += 1

            step = 0
            error_times = 0

            if flow_interval:
                sleep(flow_interval)

    export(ctx, file_format=ExportFileFormats.special.value)
