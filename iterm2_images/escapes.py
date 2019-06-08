"""Inline images and file transfers for iTerm2."""

from base64 import b64encode
import copy
from dataclasses import dataclass, field
from enum import Enum
import io
from pathlib import Path
import sys
from typing import ByteString, Optional

__all__ = ['FileEsc', 'ImageLenUnit', 'ImageDim', 'ImageEsc']


@dataclass
class FileEsc:
    """Generates escape sequences for a file transfer."""
    data: ByteString = field(default=b'', repr=False)
    name: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.data, ByteString):
            raise TypeError("'data' field must be a bytes-like object")

    @classmethod
    def open(cls, path):
        """Open a file, read it into memory, and prepare to generate escape
        sequences which encode it."""
        path = Path(path)
        name = path.parts[-1] if path.parts else None
        return cls(path.read_bytes(), name)

    def copy(self):
        """Returns a copy of the object."""
        return copy.deepcopy(self)

    @property
    def file(self):
        """Gets a new binary stream copy of the object's :attr:`data` field."""
        return io.BytesIO(self.data)

    @classmethod
    def _get_binary_stream(cls, b):
        if isinstance(b, (io.RawIOBase, io.BufferedIOBase)):
            return b
        if hasattr(b, 'buffer'):
            return cls._get_binary_stream(b.buffer)
        msg = '{} is not a binary stream nor is it convertible to one'
        raise TypeError(msg.format(type(b).__name__))

    def _write_args(self, b, args):
        b = self._get_binary_stream(b)
        fmt_args = ';'.join('{}={}'.format(k, v) for k, v in args.items())
        b.write(b'\x1b]1337;File=' + fmt_args.encode() + b':')
        b.write(b64encode(self.data))
        b.write(b'\a\n')
        b.flush()

    def write(self, b=sys.stdout.buffer):
        """Writes the escape sequences to a binary stream (by default
        `sys.stdout.buffer`)."""
        args = {}
        if self.name is not None:
            args['name'] = b64encode(self.name.encode()).decode()
        args['size'] = len(self.data)
        self._write_args(b, args)


class ImageLenUnit(Enum):
    """Represents units of measure of inline image size."""
    CELLS = ''
    PIXELS = 'px'
    PERCENT = '%'
    AUTO = 'auto'


@dataclass
class ImageDim:
    """Represents inline image sizes as a quantity with a unit of measure."""
    quantity: float = 0
    unit: ImageLenUnit = ImageLenUnit.AUTO

    def __str__(self):
        if self.unit == ImageLenUnit.AUTO:
            return self.unit.value
        return '{!s}{!s}'.format(self.quantity, self.unit.value)


@dataclass
class ImageEsc(FileEsc):
    """Generates escape sequences for an inline image."""
    width: ImageDim = field(default_factory=ImageDim)
    height: ImageDim = field(default_factory=ImageDim)
    preserve_aspect_ratio: bool = True

    def write(self, b=sys.stdout.buffer):
        args = {}
        if self.name is not None:
            args['name'] = b64encode(self.name.encode()).decode()
        args['size'] = len(self.data)
        args['width'] = str(self.width)
        args['height'] = str(self.height)
        args['preserveAspectRatio'] = int(self.preserve_aspect_ratio)
        args['inline'] = 1
        self._write_args(b, args)
