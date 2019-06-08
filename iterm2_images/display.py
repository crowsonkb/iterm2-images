#!/usr/bin/env python3

"""Displays inline images in iTerm2."""

import click
import click_pathlib

from .escapes import ImageDim, ImageEsc, ImageLenUnit

units = [x.name for x in ImageLenUnit]


@click.command()
@click.argument('image', type=click_pathlib.Path(readable=True))
@click.option('--x-qty', type=float, default=0)
@click.option('--x-unit', type=click.Choice(units, case_sensitive=False),
              default='AUTO')
@click.option('--y-qty', type=float, default=0)
@click.option('--y-unit', type=click.Choice(units, case_sensitive=False),
              default='AUTO')
def main(image, x_qty, x_unit, y_qty, y_unit):
    """The main function."""
    esc = ImageEsc(image)
    esc.width = ImageDim(x_qty, ImageLenUnit[x_unit.upper()])
    esc.height = ImageDim(y_qty, ImageLenUnit[y_unit.upper()])
    esc.write()
