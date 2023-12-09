#  Copyright (C) 2023  LTFan (aka xfqwdsj). For full copyright notice, see `main.py`.
from enum import EnumType

import click


class EnumChoice(click.Choice):
    def __init__(self, enum: EnumType):
        self.__enum = enum
        super().__init__(enum.__members__)

    def convert(self, value, param, ctx):
        return self.__enum[super().convert(value, param, ctx)].value
