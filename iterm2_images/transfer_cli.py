#!/usr/bin/env python3

"""Transfers files from the machine you are logged into to your desktop."""

import click
import click_pathlib

from .payloads import FileEsc


@click.command()
@click.argument('file', type=click_pathlib.Path(readable=True))
def main(file):
    """The main function."""
    FileEsc.open(file).write()
