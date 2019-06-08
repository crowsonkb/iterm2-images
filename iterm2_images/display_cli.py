#!/usr/bin/env python3

"""Displays inline images in iTerm2."""

import click
import click_pathlib

from .payloads import ImageDim, ImageEsc, ImageLenUnit

units = [x.name for x in ImageLenUnit]


@click.command()
@click.argument('image', type=click_pathlib.Path(readable=True))
@click.option('--x-val', type=float, default=0)
@click.option('--x-unit', type=click.Choice(units, case_sensitive=False),
              default='AUTO')
@click.option('--y-val', type=float, default=0)
@click.option('--y-unit', type=click.Choice(units, case_sensitive=False),
              default='AUTO')
@click.option('--preserve-aspect-ratio', type=bool, default=True)
def main(image, x_val, x_unit, y_val, y_unit, preserve_aspect_ratio):
    """The main function."""
    esc = ImageEsc.open(image)
    esc.width = ImageDim(x_val, ImageLenUnit[x_unit.upper()])
    esc.height = ImageDim(y_val, ImageLenUnit[y_unit.upper()])
    esc.preserve_aspect_ratio = preserve_aspect_ratio
    esc.write()
