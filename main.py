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
from typing import Annotated

import pandas as pd
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm

from precise_bet import __version__, rprint
from precise_bet.cli import export, flow, generate_data, update
from precise_bet.type import match_status_dict

notice = f'{textwrap.fill(f'PreciseBet {__version__}  Copyright (C) 2023  LTFan (aka xfqwdsj)')}\n\n' \
         f'{textwrap.fill(
             'This program comes with ABSOLUTELY NO WARRANTY.  '
             'This is free software, and you are welcome to redistribute it under certain conditions.'
         )}\n\n' \
         f'{textwrap.fill(
             'You should have received a copy of the GNU General Public License along  with this program.  '
             f'Type `{sys.argv[0]} license\' to read.  If not, see <https://www.gnu.org/licenses/>.'
         )}\n\n'

cli = typer.Typer(rich_markup_mode='markdown')


@cli.callback()
def cli_main(
        ctx: typer.Context,
        project_path: Annotated[Path, typer.Option('--project-path', '-p', help='项目路径')] = './project/'
):
    """
    一个用于获取 500.com 足球数据的命令行工具

    ## 使用方法

    1. 生成数据

       ```shell
       precise_bet generate-data --help
       ```

    2. 更新数据

       ```shell
       precise_bet update --help
       ```

    3. 导出数据

       ```shell
       precise_bet export --help
       ```

    ## 傻瓜式工作流

    ```shell
    precise_bet flow --help
    ```
    """

    ctx.ensure_object(dict)

    if project_path.exists() and not project_path.is_dir():
        confirm = Confirm.ask(f'项目路径 [bold]{project_path}[/bold] 已存在且不是目录，是否删除？', default=False)

        if not confirm:
            rprint('已取消')
            sys.exit(1)

        project_path.unlink()
        rprint('已删除')

    project_path.mkdir(exist_ok=True)
    ctx.obj['project_path'] = project_path


@cli.command()
def print_match_status_codes():
    """显示比赛状态列表"""

    df = pd.DataFrame(match_status_dict, index=['状态']).transpose().to_markdown()
    Console().print(Markdown(df))


@cli.command('license')
def show_license():
    """显示许可证信息"""

    file = typer.open_file(str(Path(__file__) / '../LICENSE'), 'r')
    rprint(file.read())
    file.close()


@cli.command()
def about():
    """显示关于信息"""

    rprint(f'PreciseBet {__version__}')


cli.command()(generate_data)
cli.command()(update)
cli.command()(export)
cli.command()(flow)

if __name__ == '__main__':
    rprint(notice)

    cli()
