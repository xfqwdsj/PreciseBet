import sys
from pathlib import Path

import click
import colorama

from cli import init_data, update, export


@click.group()
@click.pass_context
@click.option('--project-path', '-p', help='项目路径', default='./project/', type=click.Path())
def cli(ctx, project_path: str):
    colorama.init(autoreset=True)
    ctx.ensure_object(dict)
    path = Path(project_path)
    if path.exists() and not path.is_dir():
        confirm = click.confirm('项目路径 {} 已存在且不是文件夹，是否删除？'.format(project_path), default=False,
                                show_default=True, err=True)

        if not confirm:
            click.echo('已取消')
            sys.exit(1)

        path.unlink()
        click.echo('已删除')

    path.mkdir(exist_ok=True)
    ctx.obj['project_path'] = path


cli.add_command(init_data)
cli.add_command(update)
cli.add_command(export)

if __name__ == '__main__':
    cli()
