#!/usr/bin/env python3

"""Displays inline images in iTerm2."""

import argparse
from pathlib import Path

from .escapes import ImageEsc


def main():
    """The main function."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image', type=Path, help='the image file to display')
    args = ap.parse_args()
    ImageEsc(args.image).write()


if __name__ == '__main__':
    main()
