#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.

from rich.console import Console

from .info import __author__, __copyright__, __version__

rprint = Console().print
rprint_err = Console(stderr=True).print
