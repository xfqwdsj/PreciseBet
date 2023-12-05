#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import textwrap
from pathlib import Path

import click
import colorama
import pandas as pd

from precise_bet import __version__
from precise_bet.cli import generate_data, update, export
from precise_bet.data import match_status

notice = f'{textwrap.fill(f'PreciseBet {__version__}  Copyright (C) 2023  LTFan (aka xfqwdsj)')}\n\n' \
         f'{textwrap.fill('This program comes with ABSOLUTELY NO WARRANTY.  This is free software, and you are welcome '
                          'to redistribute it under certain conditions.')}\n\n' \
         f'{textwrap.fill('You should have received a copy of the GNU General Public License along  with this '
                          f'program.  Type `{sys.argv[0]} license\' to read.  If not, see '
                          '<https://www.gnu.org/licenses/>.')}\n\n'


@click.group(context_settings={'show_default': True})
@click.pass_context
@click.option('--project-path', '-p', help='项目路径', default='./project/', type=click.Path())
def cli(ctx, project_path: str):
    """
    一个用于获取 500.com 足球数据的命令行工具

    ## 使用方法

    1. 生成数据

       precise_bet generate-data --help

    2. 更新数据

       precise_bet update --help

    3. 导出数据

       precise_bet export --help
    """

    colorama.init(autoreset=True)
    ctx.ensure_object(dict)

    path = Path(project_path)
    if path.exists() and not path.is_dir():
        confirm = click.confirm(f'项目路径 {project_path} 已存在且不是目录，是否删除？', default=False, show_default=True,
                                err=True)

        if not confirm:
            click.echo('已取消')
            sys.exit(1)

        path.unlink()
        click.echo('已删除')

    path.mkdir(exist_ok=True)
    ctx.obj['project_path'] = path


@cli.command()
def print_match_status_codes():
    """显示比赛状态列表"""

    df = pd.DataFrame(match_status, index=['状态']).transpose()
    click.echo(df)


@cli.command('license')
def show_license():
    """显示许可证信息"""

    file = click.open_file(str(Path(__file__) / '../LICENSE'), 'r')
    click.echo(file.read())
    file.close()


@cli.command()
def about():
    """显示关于信息"""

    click.echo(f'PreciseBet {__version__}')


cli.add_command(generate_data)
cli.add_command(update)
cli.add_command(export)

if __name__ == '__main__':
    click.echo(notice)

    cli()
