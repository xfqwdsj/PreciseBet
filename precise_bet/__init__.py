#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from rich.console import Console

from .info import __author__, __copyright__, __version__

stdout_console = Console()
rprint = stdout_console.print
rule = stdout_console.rule

stderr_console = Console(stderr=True)
rprint_err = stderr_console.print
