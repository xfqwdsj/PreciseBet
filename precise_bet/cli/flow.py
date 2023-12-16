#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.
import typer

from precise_bet.cli.export import ExportFileFormats, export
from precise_bet.cli.generate_data import generate_data
from precise_bet.cli.update import Actions as UpdateActions, update


def flow(ctx: typer.Context, volume_number: int, full_update: bool = True, extra_interval_probability: float = 0):
    """生成数据、更新数据、导出数据"""

    generate_data(ctx, volume_number=volume_number)
    if full_update:
        update(
            ctx, action=UpdateActions.value_action.value, volume_number=volume_number,
            extra_interval_probability=extra_interval_probability, only_new=True
        )
    update(
        ctx, action=UpdateActions.handicap_action.value, volume_number=volume_number,
        extra_interval_probability=extra_interval_probability
    )
    export(ctx, file_format=ExportFileFormats.special.value)
