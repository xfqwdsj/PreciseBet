#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.
import click

import precise_bet.cli


@click.command()
@click.pass_context
@click.argument('volume-number', type=int)
@click.option('--full-update', '-f', help='完整更新', is_flag=True)
def flow(ctx, volume_number: int, full_update: bool):
    """
    生成数据、更新数据、导出数据
    """

    ctx.invoke(precise_bet.cli.generate_data, volume_number=volume_number)
    if full_update:
        ctx.invoke(precise_bet.cli.update, action='value', volume_number=volume_number, only_new=True)
    ctx.invoke(precise_bet.cli.update, action='handicap', volume_number=volume_number)
    ctx.invoke(precise_bet.cli.export, file_format='excel', special_format=True)
