#  Copyright (C) 2024  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

import traceback

import typer

from precise_bet import rprint, rule
from precise_bet.cli.export import ExportFileFormats, export
from precise_bet.cli.generate_data import generate_data
from precise_bet.cli.update import Actions as UpdateActions, update
from precise_bet.util import sleep


def flow(
    ctx: typer.Context,
    volume_number: int,
    break_hours: int = 6,
    update_value: bool = True,
    full_update: bool = True,
    execute_times: int = 1,
    flow_interval: int = 0,
    retry_times: int = 3,
    extra_interval_probability: float = 0,
    fast_mode: bool = False,
):
    """生成数据、更新数据、导出数据"""

    additional_parameter_update = {}

    if fast_mode:
        extra_interval_probability = 0
        additional_parameter_update["interval"] = 0
        additional_parameter_update["interval_offset_range"] = 0
        rprint(
            "[bold yellow]已开启快速模式，请谨慎使用。如发现数据量过大，请立即按下 Ctrl + C 中断并使用默认模式继续更新"
        )

    if retry_times < 0:
        retry_times = 0

    executed_times = 0

    step = 0
    error_times = 0

    while execute_times < 1 or executed_times < execute_times:
        terminate = False

        try:
            retry_indicator = "[bold]从中断处继续[/bold]" if step > 0 else ""
            total_indicator = (
                f" / [blue]{execute_times}[/blue]" if execute_times >= 1 else ""
            )
            rule(
                f"正在{retry_indicator}执行第 [yellow]{executed_times + 1}[/yellow]{total_indicator} 次流程"
                "（按下 [bold]Ctrl[/bold] + [bold]C[/bold] 中断）"
            )

            if step == 0:
                generate_data(ctx, volume_number=volume_number)
                step += 1

            if step == 1:
                if update_value:
                    update(
                        ctx,
                        action=UpdateActions.value_action.value,
                        volume_number=volume_number,
                        extra_interval_probability=extra_interval_probability,
                        break_hours=break_hours,
                        only_new=full_update,
                        **additional_parameter_update,
                    )
                step += 1

            if step == 2:
                update(
                    ctx,
                    action=UpdateActions.handicap_action.value,
                    volume_number=volume_number,
                    extra_interval_probability=extra_interval_probability,
                    break_hours=break_hours,
                    **additional_parameter_update,
                )
        except KeyboardInterrupt:
            terminate = True
            rule(
                "[bold red]正在中断，再次按下 [bold]Ctrl[/bold] + [bold]C[/bold] 强制中断"
            )
            break
        except Exception as e:
            error_times += 1
            if error_times > retry_times:
                raise e
            traceback.print_exception(e)
            rule(f"[bold red]发生错误，正在重试（第 {error_times} / {retry_times} 次）")
        else:
            executed_times += 1

            step = 0
            error_times = 0
        finally:
            export(ctx, file_format=ExportFileFormats.special.value)

            last = 1 <= execute_times == executed_times

            if not last and flow_interval and not terminate and error_times == 0:
                sleep(flow_interval)

    rprint("[bold green]流程执行完毕")
